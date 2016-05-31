import unittest
import fcrepo4
import logging, requests



MDATA1 = {
    'title': 'Title',
    'description': 'Description',
    'creator': 'a test script'
    }

MDATA2 = {
    'title': 'Title2',
    'description': 'Description2',
    'creator': 'a test script again'
    }

MDATA3 = {
    'title': 'Container',
    'description': 'Just a test container for slugs',
    'creator': 'a test script again'
    }

    
PATH = 'test_012'
SLUG = 'slug'

class TestGet(unittest.TestCase):

    def setUp(self):
        self.repo = fcrepo4.Repository(loglevel=logging.DEBUG)
        self.delete_path()

                
    def test_add_with_path(self):
        """Tests adding a container to an assigned path with a PUT request.

        Checks three scenarios:

        - Adding a path which doesn't already exist
        - Adding a path which already exists, raising an exception
        - Adding a path which exists with force=True, which deletes the existing
          path
"""
        g1 = self.repo.dc_rdf(MDATA1)
        g2 = self.repo.dc_rdf(MDATA2)
        root = self.repo.get(self.repo.path2uri('/'))
        self.assertIsNotNone(root)

        c = root.add_container(g1, path=PATH)
        self.assertIsNotNone(c)

        noforce = lambda: root.add_container(g2, path=PATH)
        self.assertRaises(fcrepo4.ConflictError, noforce)

        c2 = root.add_container(g2, path=PATH, force=True)
        self.assertIsNotNone(c2)

        self.repo.delete(c2.uri)
        self.repo.obliterate(c2.uri)

    def test_add(self):
        """Tests adding a container inside a container, without specifying
        the path - this uses a POST request.

        Tests three scenarios:

        - Adding a container with no slug, producing one of Fedora's auto ids
        - Adding a container with a slug which isn't already there
        - Adding a container with a slug which is already there, in which case
          Fedora assigns it an auto id and creates it anyway
        """  
        g1 = self.repo.dc_rdf(MDATA1)
        g3 = self.repo.dc_rdf(MDATA3)
        root = self.repo.get(self.repo.path2uri('/'))
        self.assertIsNotNone(root)

        # set up a determined path in which to add new containers
        c = root.add_container(g3, path=PATH)
        self.assertIsNotNone(c)

        # add a container with a slug
        slugpath = self.repo.path2uri(PATH + '/' + SLUG)
        s1 = c.add_container(g1, slug=SLUG)
        self.assertIsNotNone(s1)
        self.assertEqual(s1.uri, slugpath)

        # add a container without a slug
        s2 = c.add_container(g1)
        self.assertIsNotNone(s2)

        # add a container with a slug which already exists
        s3 = c.add_container(g1, slug=SLUG)
        self.assertIsNotNone(s3)
        self.assertNotEqual(s3.uri, slugpath)
 
                
    def tearDown(self):
        self.delete_path()

    def delete_path(self):
        uri = self.repo.path2uri(PATH)
        try:
            resource = self.repo.get(uri)
            if resource:
                self.repo.delete(uri)
                self.repo.obliterate(uri)
        except fcrepo4.ResourceError as e:
            if e.status_code != requests.codes.not_found:
                raise e

                
if __name__ == '__main__':
    unittest.main()
