"""Migrate from 1.5 to 1.6.
"""

# CMF imports
from Products.CMFCore.utils import getToolByName


class Migration(object):
    """Migrate from 1.5 to 1.6
    """

    def __init__(self, site, out):
        self.site = site
        self.out = out
        self.catalog = getToolByName(self.site, 'portal_catalog')

    def migrate(self):
        """Run migration on site object passed to __init__.
        """
        print("Migrating Quills 1.5 -> 1.6", file=self.out)
        self.removeQuillsTool()
        weblogs = self.catalog(meta_type='Weblog')
        for weblog in weblogs:
            self.migrateWeblog(weblog.getObject())

    def removeQuillsTool(self):
        """Remove quills_tool from the portal.
        """
        if self.site.hasObject('quills_tool'):
            print("Removing 'quills_tool'.", file=self.out)
            self.site.manage_delObjects(ids=['quills_tool',])
        else:
            print("'quills_tool' already removed.", file=self.out)

    def migrateWeblog(self, weblog):
        """Migrate a weblog.
        """
        msg = 'Migrating Weblog: %s'
        print(msg % '/'.join(weblog.getPhysicalPath()), file=self.out)
        self.removeRemoteBloggingAttributes(weblog)
        self.migrateWeblogViewConfiguration(weblog)
        self.movePostsToWeblogRoot(weblog)
        self.fixUpWorkflows(weblog)

    def migrateWeblogViewConfiguration(self, weblog):
        # Use direct attribute access to get hold of previously defined AT
        # schema fields on weblog, and store them with the new
        # IWeblogViewConfiguration
        pass

    def fixUpWorkflows(self, weblog):
        """Entries used to use the 'quills_workflow'. This no longer exists so
        after migration, the workflow state for entries reverts to the default
        of the default workflow. This causes all entries to appear to be
        'private' when we actually want those that were 'published' before to be
        'published' still...
        """
        weblog_path = '/'.join(weblog.getPhysicalPath())
        entries = self.catalog(path={ 'query' : weblog_path,
                                      'depth' : 1 },
                               portal_type='WeblogEntry')
        wf_tool = getToolByName(weblog, 'portal_workflow')
        for brain in entries:
            entry = brain.getObject()
            # Get the hold workflow state. Need to use a slightly different api
            # as the old workflow object is no longer around.
            old_state = wf_tool.getStatusOf(wf_id='quills_workflow', ob=entry)
            if old_state is not None:
                old_state = old_state['review_state']
                # Get the current workflow state so we can be sure not to try to do
                # this migration more than once for an entry.
                cur_state = wf_tool.getInfoFor(entry, name='review_state')
                # If it is 'published', publish the entry in its new wf.
                if old_state == 'published' and cur_state != 'published':
                    wf_tool.doActionFor(entry, 'publish')
                    msg = 'Republished weblog entry at %s'
                    print(msg % '/'.join(entry.getPhysicalPath()), file=self.out)


    def movePostsToWeblogRoot(self, weblog):
        weblog_path = '/'.join(weblog.getPhysicalPath())
        archives = self.catalog(path=weblog_path,
                                portal_type='WeblogArchive')
        entriesByPath = {}
        for archive in archives:
            entries = self.catalog(path={ 'query' : archive.getPath(),
                                          'depth' : 1 },
                                   portal_type='WeblogEntry')
            if entries:
                entriesByPath[archive.getObject()] = [ entry.getId for entry in entries ]

        for archive, entries in list(entriesByPath.items()):
            cut = archive.manage_cutObjects(entries)
            weblog.manage_pasteObjects(cut)


    def removeWeblogAuthorRole(self):
        pass

    def removeRemoteBloggingAttributes(self, weblog):
        try:
            delattr(weblog, 'metaWeblog')
            msg = "Removed 'metaWeblog' from %s."
        except AttributeError:
            msg = "No 'metaWeblog' found on %s."
        print(msg % '/'.join(weblog.getPhysicalPath()), file=self.out)
        try:
            delattr(weblog, 'blogger')
            msg = "Removed 'blogger' from %s."
        except AttributeError:
            msg = "No 'blogger' found on %s."
        print(msg % '/'.join(weblog.getPhysicalPath()), file=self.out)
