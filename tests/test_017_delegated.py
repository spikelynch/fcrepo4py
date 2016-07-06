
import unittest
import fcrepo4, fcrepotest
import logging, requests
from rdflib import Literal, URIRef
from rdflib.namespace import DC, Namespace


CPATH = 'test_017'

USER_A = 'alice'
USER_B = 'bob'

CMDATA = {
    'title': 'Container',
    'description': 'Just a test container for delegated authentication',
    'creator': 'test_017_delegated.py'
    }

MDATA1 = {
    'title': 'Newobject',
    'description': 'An object which user 1 can write to',
    'creator': 'test_017_delegated.py'
}




class TestDelegated(fcrepotest.FCRepoContainerTest):
    """Test cases for delegating identity using HTTP headers"""
    def setUp(self):
        super(TestDelegated, self).setUp(CPATH, CMDATA)

    def tearDown(self):
        super(TestDelegated, self).tearDown(CPATH)
            
    def test_delegate_identity(self):
        c = self.container

        # set up a resource which only Bob can read

        acl = self.repo.add_acl(c.uri)

        md = self.repo.dc_rdf({'title': 'My Container'})
        resource = c.add_container(md, slug='my_container')
        uri = resource.uri

        acl.grant('authb1', USER_A, fcrepo4.READ, uri)
        acl.grant('authb2', USER_A, fcrepo4.WRITE, uri)

        # try to look it up as the other user
        #direct = lambda: self.repo.get(uri)
        #self.repo.set_user(USER_B)
        #self.assertRaises(fcrepo4.ResourceError, direct)

        # set user to admin and try to delegate to first one then
        # the other user
        self.repo.set_user('fedoraAdmin')

        delegated = lambda: self.repo.get(uri, headers={ 'On-Behalf-Of': USER_A})
        getusera = delegated()
        self.assertIsNotNone(getusera)

        delegated = lambda: self.repo.get(uri, headers={ 'On-Behalf-Of': USER_B})
        self.assertRaises(fcrepo4.ResourceError, delegated)


        
if __name__ == '__main__':
    unittest.main()
