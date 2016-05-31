import unittest
import fcrepo4, fcrepotest
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

class TestPost(fcrepotest.FCRepoTest):

    def setUp(self):
        super(TestPost, self).setUp()

                

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


                
if __name__ == '__main__':
    unittest.main()
