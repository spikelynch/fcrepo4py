import unittest
import fcrepo4, fcrepotest
import logging, requests
from rdflib import Literal, URIRef
from rdflib.namespace import DC, Namespace


CMDATA = {
    'title': 'Container',
    'description': 'Just a test container for modifying triples',
    'creator': 'a test script again'
    }

MDATA1 = {
    'title': 'New container',
    'description': 'Description of new container',
    'creator': 'test_015_modify_triples.py'
}


MDATA2 = {
    'title': 'Updated title',
    'description': 'Updated description',
    'creator': 'New creator',
    'rights': 'Something about rights',
    'format': 'Format is tricky and is causing intermittent failures'
#    'format': 'Format is tricky because Python interprets it wrong'
    }
    
PCDM = Namespace('http://pcdm.org/models#')

    
    
CPATH = 'test_015'

class TestModifyTriples(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestModifyTriples, self).setUp(CPATH, CMDATA)

    def tearDown(self):
        super(TestModifyTriples, self).tearDown(CPATH)
            
    def test_update_triples(self):
        """Creates a container, set some triples on it, update them"""
        c = self.repo.get(self.repo.path2uri(CPATH))

        resource = c.add_container(self.repo.dc_rdf(MDATA1), path="resource")
        self.assertIsNotNone(resource)
        uri = resource.uri
        self.logger.info("New resource at {}".format(uri))

        for field, value in MDATA2.items():
            resource.rdf_replace(DC[field], Literal(MDATA2[field]))
        
        self.assertTrue(resource.rdf_write())

        # look it up again and test the results

        r2 = self.repo.get(resource.uri)
       
        for field, value in MDATA2.items():
            predicate = DC[field]
            self.assertEqual(str(r2.rdf_get(DC[field])), MDATA2[field])
        

    def test_intermittent_format(self):
        """Adding a DC['format'] to a container is failing sometimes."""

        for i in range(0, 10):
            self.logger.debug("Multiple format test {}".format(i))
            c = self.repo.get(self.repo.path2uri(CPATH))

            resource = c.add_container(self.repo.dc_rdf(MDATA1))
            self.assertIsNotNone(resource)
            uri = resource.uri
            self.logger.info("New resource at {}".format(uri))

            value = MDATA2['format']
            
            resource.rdf_replace(DC['format'], Literal(value))
        
            self.assertTrue(resource.rdf_write())

            r2 = self.repo.get(resource.uri)
            self.logger.debug("All rdf triples with DC.format")
            for ( s, p, o ) in r2.rdf.triples((None, DC['format'], None)):
                self.logger.debug("{} -> format -> {}".format(s, o))
            self.assertEqual(str(r2.rdf_get(DC['format'])), value)
            


            
    # def test_add_triples(self):
    #     """Creates a container and adds multiple triples with the same
    #     predicate"""

    #     c = self.repo.get(self.repo.path2uri(CPATH))

    #     resource = c.add_container(self.repo.dc_rdf(MDATA1), path="resource")
    #     self.assertIsNotNone(resource)
    #     uri = resource.uri
    #     self.logger.info("New resource at {}".format(uri))

    #     uris = [ ('http://fake.it/things/' + s) for s in [ 'one', 'two', 'three' ] ]
    
    #     for uri in uris:
    #         resource.rdf_add(PCDM['hasMember'], URIRef(uri))
            

    #     self.assertTrue(resource.rdf_write())

    #     r2 = self.repo.get(resource.uri)

    #     members = [ str(u) for u in r2.rdf_get(PCDM['hasMember']) ]
    #     for uri in uris:
    #         self.assertTrue(uri in members)
       
                                
if __name__ == '__main__':
    unittest.main()
