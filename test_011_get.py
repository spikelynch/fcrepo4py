import unittest
import fcrepo4, fcrepotest
import logging

class TestGet(fcrepotest.FCRepoTest):
        
    def test_get(self):
        root = self.repo.get(self.repo.path2uri('/'))
        self.assertIsNotNone(root)
        self.assertIsNotNone(root.rdf)

    def test_repo_mismatch(self):
        badurl = self.repo.uri + 'thisismalformed/'
        self.assertRaises(fcrepo4.URIError, self.repo.get, badurl)

        
            
if __name__ == '__main__':
    unittest.main()
