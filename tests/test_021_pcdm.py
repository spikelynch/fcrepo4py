import unittest
import fcrepo4, fcrepotest
import logging, requests
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

    #@unittest.skip("Not finished yet")
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
 
                


                
if __name__ == '__main__':
    unittest.main()
