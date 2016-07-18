import unittest
import fcrepo4, fcrepotest
import logging, requests
import filecmp

from fcrepo4.resource import Binary

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
        """Upload a binary from a file using PUT"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, path=FILE)
        self.assertIsNotNone(b)
        self.assertEqual(b.uri, cpath + '/' + FILE)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)


    def test_post_binary(self):
        """Upload a binary from a file using POST"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        BASENAME = FILE.split('/')[-1]
        b = c.add_binary(FILE)
        self.assertIsNotNone(b)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)


    def test_post_binary_slug(self):
        """Upload a binary from a file using POST with a slug"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        SLUG = 'my_new_file.jpg'
        b = c.add_binary(FILE, slug=SLUG)
        self.assertIsNotNone(b)
        self.assertEqual(b.uri, cpath + '/' + SLUG)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)


    def test_conflict_binary(self):
        """Upload binary to the same path twice without force"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, path=FILE)
        self.assertIsNotNone(b)
        noforce = lambda: c.add_binary(FILE, path=FILE)
        self.assertRaises(fcrepo4.ConflictError, noforce)


    def test_overwrite_binary(self):
        """Upload binary to the same path twice with force"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(FILE, path=FILE)
        self.assertIsNotNone(b)
        b2 = c.add_binary(FILE, path=FILE, force=True)
        self.assertIsNotNone(b2)
        


    def test_put_binary_from_url(self):
        """Add a binary from a URL using PUT"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        BASENAME = 'pic_from_url.jpg'
        b = c.add_binary(URL_BINARY, path=URL_BASENAME)
        self.assertIsNotNone(b)
        self.assertEqual(b.uri, cpath + '/' + URL_BASENAME)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)


    def test_post_binary_from_url(self):
        """Add a binary from a URL using POST"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        b = c.add_binary(URL_BINARY)
        self.assertIsNotNone(b)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)



    def test_put_binary_from_filehandle(self):
        """Tests adding a container from a filehandle using PUT"""
        cpath = self.repo.path2uri(PATH)
        c = self.repo.get(cpath)
        BPATH = 'my_binary_thing'
        b = None
        with open(FILE, 'rb') as fh:
            b = c.add_binary(fh, path=BPATH, mime=MIME_TYPE)
        self.assertIsNotNone(b)
        uri = b.uri
        b2 = self.repo.get(uri)
        self.assertIsNotNone(b2)

        

    def test_post_binary_from_filehandle(self):
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
