import unittest
import fcrepo4, fcrepotest, fcrepo4.resource
from fcrepo4.resource.webac import READ, WRITE, WEBAC_NS
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

        # should we have grant_read and grant_write?
        
        acl.grant(USER_A, READ,  uri)
        acl.grant(USER_B, READ,  uri)
        acl.grant(USER_B, WRITE, uri)

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

        self.repo.set_user('fedoraAdmin')
        acluri = acl.uri
        acl2 = self.repo.get(acluri)
        self.logger.info("acl2 = {}".format(type(acl2)))
        self.assertTrue(type(acl2) == fcrepo4.resource.webac.Acl)

        acls = acl2.acls()
        self.logger.info(acls)

    def dump_rdf(self, resource, filename):
        resource.rdf_read()
        with open(filename, 'wb') as df:
            df.write(resource.rdf.serialize(format='text/turtle'))
        self.logger.info("Dumped rdf of {} to {}".format(resource.uri, filename))
        
        
if __name__ == '__main__':
    unittest.main()
