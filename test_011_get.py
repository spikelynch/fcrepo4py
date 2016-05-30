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
    
if __name__ == '__main__':
    unittest.main()
