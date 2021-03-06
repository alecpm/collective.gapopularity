from Products.CMFCore.utils import getToolByName
from collective.gapopularity import logger

def addCatalogIndexes(context):
    """
    Add indexes to portal_catalog.
    """

    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(
        'profile-collective.gapopularity:default', 'catalog')

    catalog = getToolByName(context, 'portal_catalog')
    indexes = catalog.indexes()
    
    wanted = (
        ('ga_popularity', 'FieldIndex', None),
    )

    added = []
    for name, meta_type, extra in wanted:
        if name not in indexes:
            catalog.addIndex(name, meta_type)
            added.append(name)
            logger.info("Added %s for field %s.", meta_type, name)
        
def import_various(context):
    """
    Import step for configuration that is not handled in xml files.
    """
    
    # Only run step if a flag file is present
    if context.readDataFile('collective-gapopularity-various.txt') is not None:
        portal = context.getSite()
        addCatalogIndexes(portal)