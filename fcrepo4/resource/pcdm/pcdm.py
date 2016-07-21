
from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import Namespace
from fcrepo4.resource import Resource
from fcrepo4.exception import Error

PCDM_URI = 'http://pcdm.org/models#'
PCDM = Namespace(PCDM_URI)


class PCMDError(Error):
    """Exception class for PCDM-specific errors"""



class PCDMResource(Resource):
    """Base class for all PCDM Resources

    Methods for creating relations

    o.is_member_of(s)    - creates an [isMemberOf s] triple on o
    o.has_member(s)      - creates a [hasMember s] triple on o
    o.is_related_to(s)   - creates an [isRelatedObjectOf s] triple on o
    o.has_related_object(s) - creates an [hasRelatedObject s] on o
    o.is_file_of(s)      - isFileOf
    o.has_file(s)        - hasFile

    These methods check the RDF_RELATIONS hash in each class and throw
    a PCDMError if the relationship isn't allowed.
    
    """

    def __init__(self, repo, uri=None, metadata=None, response=None, **kwargs):
        """PCDMResource subclasses creator.

        Looks in the keyword args for pcdm relations and adds them to the
        RDF.
        """
        repo.logger.warning("In init for PCDMResource {} {}".format(uri, metadata))
        super(PCDMResource, self).__init__(repo, metadata=metadata, uri=uri, response=response)
        if response:
            return # if response, it's a repo lookup

        if self.uri:
            thisuri = URIRef(self.uri)
        else:
            thisuri = URIRef('')
        for rel, subs in self.RDF_RELATIONS.items():
            if rel in kwargs:
                if type(kwargs[rel]).__name__ in self.RDF_RELATIONS[rel]:
                    self.rdf.add((thisuri, PCDM[rel], URIRef(kwargs[rel].uri)))
                else:
                    self.repo.logger.warning("Ignoring invalid PCDM rel")
        

    
    def _check_rel(self, rel, subject):
        sclass = type(subject).__name__
        if not sclass in self.RDF_RELATIONS[rel]:
            oclass = type(self).__name__
            raise PCDMError("Bad PCDM rel: {} {} {}".format(oclass, rel, sclass))
                            
    def _add_rel(self, rel, subject):
        """Create a relation, after checking that it's allowed."""
        self._check_rel(rel, subject)
        self.rdf_add(PCDM[rel], subject.uri)
        self.rdf_write

    def is_member_of(self, subject):
        """Create a pcdm:isMemberOf link"""  
        self._add_rel('isMemberOf', subject)

    def has_member(self, subject):
        """Create a pcdm:hasMember link"""  
        self._add_rel('hasMember', subject)

    def is_related_to(self, subject):
        """Create a pcdm:isRelatedObjectOf link"""
        self._add_rel('isRelatedObjectOf', subject)

    def has_related_object(self, subject):
        """Create a pcdm:hasRelatedObject link"""
        self._add_rel('hasRelatedObject', subject)

    def is_file_of(self, subject):
        """Create a pcdm:isFileOf link"""
        self._add_rel('isRelatedObjectOf', subject)

    def has_file(self, subject):
        """Create a pcdm:hasFile link"""
        self._add_rel('hasRelatedObject', subject)


    def links(self, rel):
        """General method for returning lists of related objects"""
        return self.rdf.objects(
            subject=URIRef(self.uri),
            predicate=PDCM[rel]
        )

        
    def members(self):
        """Returns the uris of all this resource's members"""
        return self.links('hasMember')

    def memberships(self):
        """Returns the uris of all the resources this is a member of"""
        return self.links('isMemberOf')
        
    def related_objects(self):
        """Returns the uris of all this resource's relatedObjects"""
        return self.links('hasRelatedObject')

    def objects_related_to(self):
        """Returns the uris of all this resource's isRelatedObjectOf"""
        return self.links('isRelatedObjectOf')

    def files(self):
        """Returns the uris of all this resource's pcdm.Files"""
        return self.link('hasFile')

    def fileof(self):
        """Return the uris of all the resources which this is a file of"""
        return self.link('isFileOf')

    
class Collection(PCDMResource):
    """Class for a PCDM Collection

    """
    RDF_TYPE = PCDM['Collection']

    RDF_RELATIONS = {
        'hasMember': [ 'Collection', 'Object' ],
        'isMemberOf': [ 'Collection' ],
        'hasRelatedObject': [ 'Object' ]
    }

    

class Object(PCDMResource):
    """Class for a PCDM Object"""
    RDF_TYPE = PCDM['Object']

    RDF_RELATIONS = {
        'hasMember': [ 'Object' ],
        'isMemberOf': [ 'Collection' ],
        'hasRelatedObject': [ 'Object' ],
        'isRelatedObjectOf': [ 'Collection', 'Object' ],
        'hasFile': [ 'File' ]
    }
        
class File(PCDMResource):
    """Class for a PCDM File

    Note that the Fedora binary must be contained by this object
    """
    RDF_TYPE = PCDM['File']

    RDF_RELATIONS = {
        'isFileOf' : [ 'Object' ]
    }


    
