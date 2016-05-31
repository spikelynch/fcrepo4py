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

class TestPut(fcrepotest.FCRepoTest):

    def setUp(self):
        super(TestPut, self).setUp(loglevel=logging.WARNING)
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
