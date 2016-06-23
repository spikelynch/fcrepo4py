import unittest
import fcrepo4, fcrepotest
import logging, requests
from rdflib import Literal, URIRef
from rdflib.namespace import DC, Namespace


# Note- after setting ACLs on a resource, the resource's RDF is getting
# a acl: fedora:inaccessible resource

CPATH = 'test_016'

USER_A = 'alice'
USER_B = 'bob'

CMDATA = {
    'title': 'Container',
    'description': 'Just a test container for access control',
    'creator': 'a test script again'
    }

MDATA1 = {
    'title': 'Newobject',
    'description': 'An object which user 1 can write to',
    'creator': 'test_016_access.py'
}

MDATA2 = {
    'title': 'New container',
    'description': 'An object which user 2 can write to',
    'creator': 'test_016_access.py'
}



class TestACLs(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestACLs, self).setUp(CPATH, CMDATA, loglevel=logging.INFO)

    def tearDown(self):
        super(TestACLs, self).tearDown(CPATH)
            
    def test_set_acls(self):
        """Set ACLs on an object"""
        c = self.repo.get(self.repo.path2uri(CPATH))

        resource = c.add_container(self.repo.dc_rdf(MDATA1), path="resource")
        self.assertIsNotNone(resource)

        uri = resource.uri
        self.logger.info("New resource at {}".format(uri))

        acl = self.repo.add_acl(c.uri) # default path = './acl'
 
        self.assertIsNotNone(acl)

        self.logger.info("Current repo user = {}".format(self.repo.user))

        acl.grant('autha',  USER_A, fcrepo4.READ,  uri)
        acl.grant('authb1', USER_B, fcrepo4.READ,  uri)
        acl.grant('authb2', USER_B, fcrepo4.WRITE, uri)

        self.repo.set_user('alice')
        r1 = self.repo.get(uri)
        md1 = self.repo.dc_rdf({'title': 'Alice added within'})
        bad_add = lambda: r1.add_container(md1)
        self.assertRaises(fcrepo4.ResourceError, bad_add)

        self.repo.set_user('bob')
        r2 = self.repo.get(uri)
        md2 = self.repo.dc_rdf({'title': 'Bob added within'})
        r3 = r2.add_container(md2)
        self.assertIsNotNone(r3)


    def dump_rdf(self, resource, filename):
        resource.rdf_read()
        with open(filename, 'wb') as df:
            df.write(resource.rdf.serialize(format='text/turtle'))
        self.logger.info("Dumped rdf of {} to {}".format(resource.uri, filename))
        
        
if __name__ == '__main__':
    unittest.main()
