import unittest
import fcrepo4, fcrepotest
import logging, requests
from rdflib import Graph
from rdflib.namespace import Namespace

import fcrepo4.resource.pcdm as pcdm

MDATA = {
    'title': 'A container to run PCDM tests in',
    'description': 'A test container',
    'creator': 'test_021_pcdm.py'
}

PCDM_URI = 'http://pcdm.org/models#'
PCDM = Namespace(PCDM_URI)



    
PATH = 'test_021'
SLUG = 'slug'

class TestPcdm(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        # set up a container at PATH
        super(TestPcdm, self).setUp(PATH, MDATA)

    def tearDown(self):
        super(TestPcdm, self).tearDown(PATH)

    def test_collection(self):
        """Add a pcdm:Collection"""

        MDATA2 = {
            'title': 'A PCDM collection',
            'description': 'A PCDM collection of Objects and stuff',
            'creator': 'test_021_pcdm.py'
        }
        
        g = self.repo.dc_rdf(MDATA2)
        c = self.container.add(pcdm.Collection(self.repo, metadata=g))
        self.assertIsNotNone(c)

        uri = c.uri

        c2 = self.repo.get(uri)
        self.assertIsNotNone(c2)
        
        md = c2.dc()
        for dcfield in [ 'title', 'description', 'creator' ]:
            self.assertEqual(md[dcfield], MDATA2[dcfield])

        self.assertTrue(PCDM['Collection'] in c2.rdf_types())
            
    def test_object(self):
        """Add a pcdm:Object"""

        MDATA2 = {
            'title': 'A PCDM Object',
            'description': 'A PCDM Object',
            'creator': 'test_021_pcdm.py'
        }
        
        g = self.repo.dc_rdf(MDATA2)
        c = self.container.add(pcdm.Object(self.repo, metadata=g))
        self.assertIsNotNone(c)

        uri = c.uri

        c2 = self.repo.get(uri)
        self.assertIsNotNone(c2)
        
        md = c2.dc()
        for dcfield in [ 'title', 'description', 'creator' ]:
            self.assertEqual(md[dcfield], MDATA2[dcfield])

        self.assertTrue(PCDM['Object'] in c2.rdf_types())
 
                
    def test_membership(self):
        """Add a pcdm:Collection and some pcdm:Objects as members"""

        MDATA2 = {
            'title': 'A PCDM Collection',
            'description': 'A PCDM Collection',
            'creator': 'test_021_pcdm.py'
        }

        MDATA3 = {
            'title': 'A PCDM Object',
            'description': 'A PCDM Object',
            'creator': 'test_021_pcdm.py'
        }

        g1 = self.repo.dc_rdf({ 'title': 'Collections' })
            
        collections = self.container.add_container(metadata=g1, path='collections')
        g2 = self.repo.dc_rdf({ 'title': 'Objects' })
        objects = self.container.add_container(metadata=g2, path='objects')
            
        g = self.repo.dc_rdf(MDATA2)
        c = collections.add(pcdm.Collection(self.repo, metadata=g))
        self.assertIsNotNone(c)
        coll_uri = c.uri

        obj_uris = []
        for i in range(0, 6):
            md = MDATA3
            md['title'] += ' ' + str(i)
            g = self.repo.dc_rdf(md)
            o = pcdm.Object(self.repo, metadata=g, isMemberOf=c)
            objects.add(o)
            obj_uris.append(o.uri)

        # this has created memberships on the objects, not the collection.
        for uri in obj_uris:
            o = self.repo.get(uri)
            self.assertIsNotNone(o)
            ms = list(o.memberships())
            self.assertEqual(str(ms[0]), coll_uri)

        # add links from the collection to each of the objects

        for uri in obj_uris:
            o = self.repo.get(uri)
            c.has_member(o)

        # now we can find objects using the members method

        members = [ str(m) for m in c.members() ]

        self.repo.logger.warning(members)
        for uri in obj_uris:
            self.assertTrue(uri in members)
        


                
if __name__ == '__main__':
    unittest.main()
