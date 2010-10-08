from Acquisition import aq_base
from zope.component import adapts
from zope.interface import implements
from plone.indexer import indexer
from collective.gapopularity.interfaces import IPopularity, \
    IPopularityMarker

class Popularity(object):
    implements(IPopularity)
    adapts(IPopularityMarker)
    
    def __init__(self, context):
        self.context = context
    
    def _get_ga_popularity(self):
        return getattr(self.context, 'ga_popularity', 0)
        
    def _set_ga_popularity(self, popularity):
        self.context.ga_popularity = popularity
        
    ga_popularity = property(_get_ga_popularity, _set_ga_popularity)
                    
@indexer(IPopularityMarker)
def ga_popularity_indexer(obj):
    popularity = IPopularity(aq_base(obj), None)
    if popularity:
        return popularity.ga_popularity
    return None
