import unittest
import fcrepo4

class TestConnect(unittest.TestCase):
        
    def test_connect(self):
        """Connect to repository"""
        repo = fcrepo4.Repository()
        repo.set_user('fedoraAdmin')
        self.assertIsNotNone(repo)
        res = repo.get(repo.path2uri('/'))
        self.assertIsNotNone(res)
    
if __name__ == '__main__':
    unittest.main()
