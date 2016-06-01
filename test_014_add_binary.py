import unittest
import fcrepo4, fcrepotest
import logging, requests



MDATA1 = {
    'title': 'Bird',
    'description': 'A picture of a bird',
    'creator': 'a test script'
    }


MDATA2 = {
    'title': 'Container',
    'description': 'Just a test container for binaries',
    'creator': 'a test script again'
    }

    
PATH = 'test_014'
FILE = 'bird.jpg'


class TestPutBinary(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestPutBinary, self).setUp(PATH, MDATA2)

    def tearDown(self):
        super(TestPutBinary, self).tearDown(PATH)
                
    def test_put_binary(self):
        """Tests adding a container to an assigned path with a PUT request.

"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, slug=FILE)
        self.assertIsNotNone(b)
        self.assertEqual(b.uri, cpath + '/' + FILE)
                

                
if __name__ == '__main__':
    unittest.main()