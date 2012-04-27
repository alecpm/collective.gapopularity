from zope.interface import implements
from collective.gapopularity.interfaces import IPopularityUpdatedEvent

class PopularityUpdatedEvent(object):
    """
    Event indicating that the popularity of objects has been updated from
    Google Analytics.
    """
    
    implements(IPopularityUpdatedEvent)
    
    def __init__(self, uids):
        self.uids = uids
