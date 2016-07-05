import unittest
import fcrepo4, fcrepotest
import logging

MDATA1 = {
    'title': 'Get',
    'description': 'Container for testing Get',
    'creator': 'a test script'
    }

MDATA2 = {
    'title': 'container',
    'description': 'something to get',
    'creator': 'a test script'
    }

    
PATH = 'test_011'
SLUG = 'test_get'


class TestGet(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestGet, self).setUp(PATH, MDATA1)

    def tearDown(self):
        super(TestGet, self).tearDown(PATH)

    def test_get(self):
        """Get a container's metadata"""
        root = self.repo.get(self.repo.path2uri('/'))
        self.assertIsNotNone(root)
        self.assertIsNotNone(root.rdf)

        c1 = self.container.add_container(self.repo.dc_rdf(MDATA2), slug=SLUG)
        c1path = self.repo.path2uri(PATH + '/' + SLUG)

        c2 = self.repo.get(c1path)
        self.assertIsNotNone(c2)

        md2 = c2.dc()

        for dcfield in [ 'title', 'description', 'creator' ]:
            self.assertEqual(md2[dcfield], MDATA2[dcfield])


    def test_missing(self):
        """Get a path which doesn't exist"""
        missing = self.repo.path2uri(PATH + '/' + SLUG + "_missing")
        r = self.repo.get(missing)
        self.assertIsNone(r)

    def test_repo_mismatch(self):
        """Get a malformed path"""
        badurl = self.repo.uri + 'thisismalformed/'
        self.assertRaises(fcrepo4.URIError, self.repo.get, badurl)

        
            
if __name__ == '__main__':
    unittest.main()
