import unittest
import fcrepo4

class TestConnect(unittest.TestCase):
        
    def test_connect(self):
        repo = fcrepo4.Repository()
        self.assertIsNotNone(repo)
        res = repo.get('/')
        self.assertIsNotNone(res)
    
if __name__ == '__main__':
    unittest.main()
