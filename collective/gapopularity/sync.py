import traceback
from zope.publisher.browser import BrowserPage
from zope.component import getMultiAdapter, getUtility
from zope.schema.interfaces import IVocabularyFactory
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.gapopularity import logger
from collective.gapopularity.interfaces import IPopularityMarker, \
    IPopularity
from datetime import date, timedelta

class UpdatePopularity(BrowserPage):
    """
    Update the popularity of Plone objects based on data from Google Analytics.
    """
    
    def __call__(self, **kwargs):
        
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
        
        # Get brains for all the objects.
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.searchResults({
            'object_provides': IPopularityMarker.__identifier__,
            'path': '/'.join(self.context.getPhysicalPath()),
        })
        
        # Get a list of types that need an explicit view action in the URL.
        portal_properties = getToolByName(self.context, 'portal_properties')
        site_properties = portal_properties.get('site_properties')
        use_view_action = site_properties.getProperty('typesUseViewActionInListings', [])
        
        updated = 0
                        
        for brain in brains:
            url = brain.getURL().replace(self.request.SERVER_URL, '').strip()
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
                    updated += 1
                    
        return 'Successfully updated popularity for %i objects.' % updated
            
