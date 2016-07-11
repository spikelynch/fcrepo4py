
from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import Namespace
from fcrepo4.resource import Resource, resource_register

WEBAC_URL = 'http://www.w3.org/ns/auth/acl#'
WEBAC_NS = Namespace(WEBAC_URL)

READ = 'Read'
WRITE = 'Write'


class Acl(Resource):
    """Class representing a Web AC ACL"""


    def __init__(self, repo, uri, metadata=None, response=None):
        """Creator has to set the auths list"""
        super(Acl, self).__init__(repo, uri, metadata=metadata, response=response)
        self.auths = []
        
    def auth_path(self, user, access):
        """Standard path for an auth granting user access"""
        return self.repo.pathconcat(self.uri, user + '_' + access)

            
    def grant(self, user, access, uri):
        """Grant a user an access level over a resource, specified by its
        URI. Also adds a triple to the resource at uri pointing to this ACL
        as its access source.
        """
        resource = self.repo.get(uri) # will raise ResourceError if not found

        # in the example on the FC4 wiki, the order of creation is:
        # - the acl resource
        # - the resource to be protected (refers to the acl)
        # - the authentication resource (refers to the acl and the protected)

        # https://wiki.duraspace.org/display/FEDORA4x/Quick+Start+with+WebAC, 
        resource.rdf.bind('acl', WEBAC_NS)
        resource.rdf_add(WEBAC_NS['accessControl'], URIRef(self.uri))
        resource.rdf_write()
    
        authuri = self.auth_path(user, access)
        auth = Auth(self.repo, authuri)
        auth.put(user, access, uri)
        self.auths.append(auth)

        
    def revoke(self, user, access, uri):
        """Revoke a user's access level to a resource, specified by its
        URI. Doesn't remove the triple pointing to this ACL from the URI because
        there may be other auths, so it's not symmetrical.
        """
        resource = self.repo.get(uri) 
        auth_uri = self.auth_path(user, access)

        if self.get(auth_uri):
            self.repo.delete(auth_uri)
            self.repo.obliterate(auth_uri)


            


                        
    def acls(self):
        """Returns all of the ACLs permissions as a dict-by-uri-then-user

        {
            uri1: { u1: [ 'Read' ], u2: [ 'Read', 'Write' ] },
            uri2: { u1: ... }
        }
        """
        acls = {}
        for uri in self.children():
            auth = self.repo.get(uri)
            if auth:
                agent, access, uri = auth.get()
                if uri not in acls:
                    acls[uri] = {}
                if agent not in acls[uri]:
                    acls[uri][agent] = []
                acls[uri][agent].append(access)
        return acls
        
    def permissions(self, uri):
        """Returns the permissions on a uri as a dict-by-action:

        {
            'Read': [ u1, u2, u3 ],
            'Write': [ u1, u2 ]
        }
        """
        pass

    def users(self, uri):
        """Returns the permissions on a uri as a dict-by-user:

        {
            u1: [ 'Read', 'Write' ],
            u2: [ 'Read', 'Write' ],
            u3: [ 'Write'
        }
        """
        pass


resource_register(WEBAC_NS['Acl'], Acl)



class Auth(Resource):
    """A Resource which represents an authentication in an ACL.

    The Auth class encapsulates the logic for reading and writing the RDF
    triples which WebAC stores.
    """
    
    
    def put(self, agent, access, uri):
        """Generates the correct RDF for granting agent access to the
        subject (URI) and PUTs it to the repository, using force"""

        self.agent = agent
        self.access = access
        self.accessto = uri
        self.rdf = Graph()
        self.rdf.bind('acl', WEBAC_NS)
        this = URIRef('')
        self.rdf.add( ( this, RDF.type, WEBAC_NS['Authorization']) )
        self.rdf.add( ( this, WEBAC_NS['accessTo'], URIRef(uri) ) )
        self.rdf.add( ( this, WEBAC_NS['mode'],     WEBAC_NS[access] ) )
        self.rdf.add( ( this, WEBAC_NS['agent'],    Literal(agent) ) )
        super(Auth, self).put()
        
    def get(self):
        """Decodes the RDF into a tuple of (agent, access, subject)"""
        self.accessto = str(self.rdf_get(WEBAC_NS['accessTo']))
        access = self.rdf_get(WEBAC_NS['mode'])
        if access[-4:] == 'Read':
            self.access = READ
        else:
            self.access = WRITE
        self.agent = str(self.rdf_get(WEBAC_NS['agent']))
        return ( self.agent, self.access, self.accessto )


resource_register(WEBAC_NS['Authorization'], Auth)
