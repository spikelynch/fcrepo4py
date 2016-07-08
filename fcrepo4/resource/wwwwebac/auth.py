from fcrepo4.resource import Resource


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
