import unittest
import fcrepo4
import logging

class TestGet(unittest.TestCase):
        
    def test_get(self):
        repo = fcrepo4.Repository(loglevel=logging.DEBUG)
        self.assertIsNotNone(repo)
        root = repo.get(repo.path2uri('/'))
        self.assertIsNotNone(root)
        self.assertIsNotNone(root.rdf)

    def test_repo_mismatch(self):
        repo = fcrepo4.Repository(loglevel=logging.DEBUG)
        self.assertIsNotNone(repo)
        badurl = repo.uri + 'thisismalformed/'
        self.assertRaises(fcrepo4.URIError, repo.get, badurl)

    def test_tombstone(self):
        repo = fcrepo4.Repository(loglevel=logging.DEBUG)
        self.assertIsNotNone(repo)
        c = repo.ensure_container(repo.path2uri('/ensured'))
        self.assertIsNotNone(c)
        
            
if __name__ == '__main__':
    unittest.main()
