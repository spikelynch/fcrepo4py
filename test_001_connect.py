import unittest
import fcrepo4
import requests

class TestConnect(unittest.TestCase):
        
    def test_connect(self):
        repo = fcrepo4.Repository()
        self.assertIsNotNone(repo)
        response = repo.get('/')
        self.assertTrue(response.status_code, requests.codes.ok)
    
if __name__ == '__main__':
    unittest.main()
