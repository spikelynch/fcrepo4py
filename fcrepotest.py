import unittest, logging
import fcrepo4

class FCRepoTest(unittest.TestCase):
    """Test case which sets up a repository connection"""
    def setUp(self, loglevel=logging.WARNING):
        self.repo = fcrepo4.Repository(loglevel=loglevel)


class FCRepoContainerTest(FCRepoTest):
    """Test case which ensures that a path will exist in which to do stuff
       and which destroys it at the end"""
    
    def setUp(self, path, metadata):
        super(FCRepoContainerTest, self).setUp()
        # set up a determined path in which to add new containers
        g = self.repo.dc_rdf(metadata)
        root = self.repo.get(self.repo.path2uri('/'))
        self.container = root.add_container(g, path=path, force=True)
        self.assertIsNotNone(self.container)
        
                
    def tearDown(self, path):
        uri = self.repo.path2uri(path)
        self.repo.delete(uri)
        self.repo.obliterate(uri)

