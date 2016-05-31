import unittest
import fcrepo4, fcrepotest
import logging, requests



MDATA1 = {
    'title': 'Title',
    'description': 'Description',
    'creator': 'a test script'
    }


MDATA2 = {
    'title': 'Container',
    'description': 'Just a test container for slugs',
    'creator': 'a test script again'
    }

    
PATH = 'test_013'
SLUG = 'slug'

class TestPost(fcrepotest.FCRepoTest):

    def setUp(self):
        super(TestPost, self).setUp(loglevel=logging.DEBUG)
        # set up a determined path in which to add new containers
        g = self.repo.dc_rdf(MDATA2)
        root = self.repo.get(self.repo.path2uri('/'))
        self.container = root.add_container(g, path=PATH, force=True)
        self.assertIsNotNone(self.container)


        
    def test_add(self):
        """Tests adding a container inside a container, without specifying
        the path - this uses a POST request.

        Tests three scenarios:

        - Adding a container with no slug, producing one of Fedora's auto ids
        - Adding a container with a slug which isn't already there
        - Adding a container with a slug which is already there, in which case
          Fedora assigns it an auto id and creates it anyway
        """  

        g = self.repo.dc_rdf(MDATA1)
        
        # add a container with a slug
        slugpath = self.repo.path2uri(PATH + '/' + SLUG)
        s1 = self.container.add_container(g, slug=SLUG)
        self.assertIsNotNone(s1)
        self.assertEqual(s1.uri, slugpath)

        # add a container without a slug
        s2 = self.container.add_container(g)
        self.assertIsNotNone(s2)

        # add a container with a slug which already exists
        s3 = self.container.add_container(g, slug=SLUG)
        self.assertIsNotNone(s3)
        self.assertNotEqual(s3.uri, slugpath)
 
                
    def tearDown(self):
        uri = self.repo.path2uri(PATH)
        self.repo.logger.warning("teardown uri = {}".format(uri))
        self.repo.delete(uri)
        self.repo.obliterate(uri)


                
if __name__ == '__main__':
    unittest.main()
