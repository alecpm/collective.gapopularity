import traceback
from Acquisition import aq_parent, aq_inner
from zope.publisher.browser import BrowserPage
from zope.component import getMultiAdapter, getUtility
from zope.event import notify
from zope.interface import alsoProvides
from zope.schema.interfaces import IVocabularyFactory
from Products.CMFCore.interfaces import ISiteRoot, IContentish
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.gapopularity import logger
from collective.gapopularity.events import PopularityUpdatedEvent
from collective.gapopularity.interfaces import IPopularityMarker, \
    IPopularity
from datetime import date, timedelta
try:
    from plone.protect.interfaces import IDisableCSRFProtection
except ImportError:
    from zope.interface import Interface as IDisableCSRFProtection


class UpdatePopularity(BrowserPage):
    """
    Update the popularity of Plone objects based on data from Google Analytics.
    """
    
    def __call__(self, **kwargs):
        alsoProvides(self.request, IDisableCSRFProtection)
        try:
            return self.sync_popularity(**kwargs)
        except:
            catch_errors = kwargs.get('catch_errors',
                self.request.get('catch_errors', False))
            if catch_errors:
                message = traceback.format_exc()
                logger.error(message)
                email = kwargs.get('email', self.request.get('email', None))
                if email:
                    # If we have an e-mail address, we try to send
                    # the traceback to that address.
                    MailHost = getToolByName(self.context, 'MailHost')
                    subject = u'GA Popularity Update Failure: %s' % self.context.Title()
                    sender = getUtility(ISiteRoot).email_from_address or email
                    try:
                        MailHost.secureSend(message, email, sender,
                            subject=subject, subtype='plain', charset='utf-8')
                    except:
                        pass
            else:
                raise
        
    def sync_popularity(self, **kwargs):
        """
        Query Google and perform the update.
        """
        
        analytics_tool = getToolByName(self.context, 'portal_analytics', None)
        if not analytics_tool:
            return 'collective.googleanalytics is not installed.'
            
        report_name = kwargs.get('report', self.request.get('report', None))
        if report_name in analytics_tool.objectIds():
            report = analytics_tool[report_name]
        else:
            return 'The report "%s" could not be found.' % report_name
            
        profile = kwargs.get('profile', self.request.get('profile', None))
        if not profile:
            return 'No profile specified.'
            
        # Get the vocabulary of profiles.
        vocab_factory = getUtility(IVocabularyFactory,
            name='collective.googleanalytics.Profiles')
        vocab = vocab_factory(self.context)
        
        try:
            profile_ids = vocab.getTermByToken(profile).value
        except LookupError:
            return 'No profile named "%s" is available.' % profile
                        
        # Set the start and end date in the request.
        try:
            days = int(kwargs.get('days', self.request.get('days', 365)))
        except ValueError:
            days = 365
        
        end = date.today()
        start = end - timedelta(days=days)
        self.request.set('end_date', end.strftime('%Y%m%d'))
        self.request.set('start_date', start.strftime('%Y%m%d'))
        
        # Set the profile ID.
        self.request.set('profile_ids', profile_ids)
        
        # Get the renderer for the report.
        renderer = getMultiAdapter(
            (self.context, self.request, report),
            interface=IAnalyticsReportRenderer
        )
        
        # Get the results of the query.
        popularity_map = dict(renderer.rows())
        
        # Get a list of types that need an explicit view action in the URL.
        portal_properties = getToolByName(self.context, 'portal_properties')
        site_properties = portal_properties.get('site_properties')
        use_view_action = site_properties.getProperty('typesUseViewActionInListings', [])
        
        updated = []
        
        # See if we need to strip a prefix from the URL. This is useful
        # for running the sync from a cron job.
        prefix = kwargs.get('prefix', self.request.get('prefix', None))
        
        # Determine whether we are querying for all objects that provide the
        # marker interface or attempting to traverse to the URLs returned
        # by Google Analytics.
        traverse = kwargs.get('traverse', self.request.get('traverse', None))
        if traverse:
            # Attempt to traverse to each URL.
            for path, popularity in popularity_map.items():
                if prefix and path.startswith(prefix):
                    path = path[len(prefix):]
                obj = self.context.restrictedTraverse(path.lstrip('/'), None)
                if not IContentish.providedBy(obj):
                    obj = aq_parent(aq_inner(obj))
                    if not IContentish.providedBy(obj):
                        continue
                adapter = IPopularity(obj, None)
                if adapter:
                    if not adapter.ga_popularity == popularity:
                        adapter.ga_popularity = popularity
                        obj.reindexObject(['ga_popularity'])
                        updated.append(obj.UID())
                
        else:        
            # Get brains for all the objects.
            catalog = getToolByName(self.context, 'portal_catalog')
            brains = catalog.searchResults({
                'object_provides': IPopularityMarker.__identifier__,
                'path': '/'.join(self.context.getPhysicalPath()),
            })
                                    
            for brain in brains:
                url = brain.getURL().replace(self.request.SERVER_URL, '').strip()
                if prefix and url.startswith(prefix):
                    url = url[len(prefix):]
                if brain.portal_type in use_view_action:
                    url += '/view'
                popularity = popularity_map.get(url, 0)
                popularity += popularity_map.get(url + '/', 0)
            
                # Set the popularity if it has changed.
                if popularity != brain.ga_popularity:
                    obj = brain.getObject()
                    adapter = IPopularity(obj, None)
                    if adapter:
                        adapter.ga_popularity = popularity
                        obj.reindexObject(['ga_popularity'])
                        updated.append(brain.UID)
                        
        if updated:
            notify(PopularityUpdatedEvent(updated))
        
        return 'Successfully updated popularity for %i objects.' % len(updated)
            
