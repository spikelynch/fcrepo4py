import unittest
import fcrepo4

class TestPaths(unittest.TestCase):
        
    def test_paths(self):
        """Path-to-uri and uri-to-path conversions"""
        repo = fcrepo4.Repository()
        self.assertIsNotNone(repo)
        path = 'this/is/a/made/up/path'
        uri = repo.path2uri(path)
        self.assertEqual(uri, repo.uri + 'rest/' + path)
        path2 = repo.uri2path(uri)
        self.assertEqual(path2, path)
    
if __name__ == '__main__':
    unittest.main()
