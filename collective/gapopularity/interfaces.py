from zope.interface import Interface
from zope import schema
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

class IPopularityMarker(Interface):
    """
    Marker interface to indicate that the popuplarity of the object is being
    tracked.
    """

class IPopularity(Interface):
    """
    The popularity of the object according to Google Analytics.
    """
    
    ga_popularity = schema.ASCIILine(
        title=u'Popularity',
    )
    
class IPopularityLayer(IDefaultBrowserLayer):
    """
    Browser layer for collective.gapopularity.
    """