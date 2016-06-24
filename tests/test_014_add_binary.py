import unittest
import fcrepo4, fcrepotest
import logging, requests
import filecmp


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
FILE = 'tests/bird.jpg'
FILE2 = 'tests/bird2.jpg'
MIME_TYPE = 'image/jpeg'

URL_BINARY = 'http://apod.nasa.gov/apod/image/1605/Trumpler14c_ward.jpg'
URL_BASENAME = URL_BINARY.split('/')[-1]

OUTFILE = 'tests/bird2.jpg'

class TestPutBinary(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestPutBinary, self).setUp(PATH, MDATA2)

    def tearDown(self):
        super(TestPutBinary, self).tearDown(PATH)
            
    def test_put_binary(self):
        """Tests uploading a binary with a PUT request"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, path=FILE)
        self.assertIsNotNone(b)
        self.assertEqual(b.uri, cpath + '/' + FILE)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)

    def test_post_binary(self):
        """Tests uploading a binary with a POST request"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        BASENAME = FILE.split('/')[-1]
        b = c.add_binary(FILE, slug=BASENAME)
        self.assertIsNotNone(b)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)

                
    def test_conflict_binary(self):
        """Tests trying to upload the same path twice without force"""

        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, path=FILE)
        self.assertIsNotNone(b)
        noforce = lambda: c.add_binary(FILE, path=FILE)
        self.assertRaises(fcrepo4.ConflictError, noforce)

    def test_overwrite_binary(self):
        """Tests trying to upload the same path twice with force"""

        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, path=FILE)
        self.assertIsNotNone(b)
        b2 = c.add_binary(FILE, path=FILE, force=True)
        self.assertIsNotNone(b2)
        

    def test_binary_from_url(self):
        """Tests adding a container to an assigned path with a PUT request.

"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        BASENAME = 'pic_from_url.jpg'
        b = c.add_binary(URL_BINARY, path=URL_BASENAME)
        self.assertIsNotNone(b)
        self.assertEqual(b.uri, cpath + '/' + URL_BASENAME)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)


    def test_binary_from_filehandle(self):
        """Tests adding a container from a filehandle with a POST"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        BASENAME = FILE.split('/')[-1]
        b = None
        with open(FILE, 'rb') as fh:
            b = c.add_binary(fh, slug=BASENAME, mime=MIME_TYPE)
        self.assertIsNotNone(b)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)

                                
if __name__ == '__main__':
    unittest.main()
