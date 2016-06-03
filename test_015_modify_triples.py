import unittest
import fcrepo4, fcrepotest
import logging, requests
from rdflib import Literal, URIRef
from rdflib.namespace import DC
from fcrepo4 import REPLACE, APPEND


MDATA = {
    'title': 'Container',
    'description': 'Just a test container for modifying triples',
    'creator': 'a test script again'
    }

    
CPATH = 'test_015'

class TestModifyTriples(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestModifyTriples, self).setUp(CPATH, MDATA)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)

    def tearDown(self):
        super(TestModifyTriples, self).tearDown(CPATH)
            
    def test_update_triples(self):
        """Creates a container, set some triples on it, update them"""
        c = self.repo.get(self.repo.path2uri(CPATH))

        dcdict = {
            'title': 'New container',
            'description': 'Description of new container',
            'creator': 'test_015_modify_triples.py'
            }

        resource = c.add_container(self.repo.dc_rdf(dcdict), path="resource")
        self.assertIsNotNone(resource)
        uri = resource.uri
        self.logger.info("New resource at {}".format(uri))
        new_title = "Updated title"
        new_desc = "Updated description"
        new_creator = "New creator"
        new_rights = "Something about rights"

        changes = [
            ( REPLACE, DC['title'],       Literal(new_title)  ),
            ( REPLACE, DC['description'], Literal(new_desc)   ),
            ( REPLACE, DC['creator'],     Literal(new_creator)) ,
            ( REPLACE, DC['rights'],      Literal(new_rights) ),
        ]

        resource.update(changes)

        # look it up again and test the results

        r2 = self.repo.get(resource.uri)
        
        self.assertEqual(str(r2.rdf_get(DC['title'])),       new_title   )
        self.assertEqual(str(r2.rdf_get(DC['description'])), new_desc    )
        self.assertEqual(str(r2.rdf_get(DC['creator'])),     new_creator )
        self.assertEqual(str(r2.rdf_get(DC['rights'])),      new_rights  )
                                
if __name__ == '__main__':
    unittest.main()
