#import requests, mimetypes, json, yaml, logging, re

import requests, logging
from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC

from fcrepo4.exception import ResourceError

# the following are what the code uses as a serialisation format for
# RDF between the repository and the Resource objects: the first is
# the mime type requested of the server, the second is the rdflib parser
    
RDF_MIME = 'text/turtle'
RDF_PARSE = 'turtle'    

RDF_ADD = 0
RDF_REPLACE = 1
RDF_REMOVE = 2

LDP_CONTAINS = URIRef('http://www.w3.org/ns/ldp#contains')


DC_FIELDS = [
    'contributor',
    'coverage',
    'creator',
    'date',
    'description',
    'format',
    'identifier',
    'language',
    'publisher',
    'relation',
    'rights',
    'source',
    'subject',
    'title',
    'type'
    ]

# registry of RDF types and resource subclasses

rdf2class = {}

logger = logging.getLogger(__name__)


def resource_register(rdf_type, resource_class):
    rdf2class[rdf_type] = resource_class
    logger.info("Registered class {} as RDF type {}".format(resource_class, rdf_type))
    

    

class ResourceMeta(type):
    """Metaclass to automagically register Resource subclasses."""
    def __new__(meta, name, bases, class_dict):
        """Register a Resource subclass

        If a subclass of Resource has a class variable RDF_TYPE, this
        intercepts it and registers the RDF type against the class in the
        registry dict.
        """
        cls = type.__new__(meta, name, bases, class_dict)
        if hasattr(cls, 'RDF_TYPE'):
            resource_register(cls.RDF_TYPE, cls)
        return cls


def typedResource(rdf):
    """Take an RDF graph and return the right Resource class

    This is probably still broken: I've assumed that all RDF.type triples
    have the Fedora node as their subject
    """
    newclass = None
    for s, o in rdf.subject_objects(predicate=RDF.type):
        if o in rdf2class:
            newclass = rdf2class[o]
    if newclass:
        return newclass
    else:
        return Resource

            

class Resource(object, metaclass=ResourceMeta):
    """Object representing a resource.

Attributes
    repo (Repository): the repository
    uri (str): its URI
    rdf (Graph): its RDF graph
    response (Response): the requests.Response object, if available

    """

    RDF_TYPE = None
    
    
    def __init__(self, repo, uri=None, metadata=None, response=None):
        """
Create a new object representing a Resource (or a specialised subclass).

The only thing a Resource must have is a repository.  For example, you can
now create a Resource without its own URI, and then add it to a container

    resource = Resource(repo, metadata=graph)
    resource.create(container=container)

The uri will be container.uri/whatever-fedora-gives and will be set on the
resource. See the create() method's docs for details.

"""
        self.repo = repo
        self.uri = uri
        self.rdf = None
        if metadata:
            if type(metadata) == Graph:
                self.rdf = metadata
            else:
                self.repo.logger.warning("Passed raw metadata to Resource")
                pass
        if response:
            self.response = response
        else:
            self.response = None
        self.changes = []

        
        

    def dc(self):
        """Extracts all DC values and returns a dict"""
        dc = {}
        for field in DC_FIELDS:
            value = self.rdf_get(DC[field])
            if value:
                dc[field] = str(value)
        return dc

        
    def data(self):
        """Returns the data in the resource as a single lump"""
        if self.response:
            return self.response.text
        else:
            return None

    def stream(self):
        """Returns an object from which the data in the resource can be
        streamed"""
        if self.response:
            return self.response.raw
        else:
            return None
        
    def _parse_rdf(self, rdf):
        """Parse the serialised RDF content from FC as an rdflib Graph"""
        self.rdf = Graph()
        self.rdf.parse(data=rdf, format=RDF_PARSE)


    def create(self, container, metadata=None, slug=None, path=None, force=None):
        """Core method for creating Fedora resources.

Parameters

    container: Resource or uri of the container in which to create it
    metadata: rdf graph
    path: path relative to container
    slug: preferred path
    force: whether to delete container/path if it already exits
   
This was taken over from repository.add_container because I decided that the
code for building resources belonged in the Resource class.
    
        """
        if metadata:
            self.rdf = metadata
        self._ensure_rdf_type()
        if type(container) == str:
            uri = container
        else:
            uri = container.uri
        headers = { 'Content-Type': RDF_MIME }
        if path:
            method = 'PUT'
            uri = self.repo.pathconcat(uri, path)
            self.repo._ensure_path(uri, force)
        else:
            method = 'POST'
            if slug:
                headers['Slug'] = slug
        rdf_text = self.rdf.serialize(format=RDF_MIME)

        return self._create_api(uri, method, headers, rdf_text)



    def _create_api(self, uri, method, headers, data):
        """Internal method that does the api call, shared between Resource
        and Binary (and anyone else)"""
        
        response = self.repo.api(uri, method=method, headers=headers, data=data)
        if response.status_code == requests.codes.no_content or response.status_code == requests.codes.created:
            self.uri = response.text
            return self
        else:
            message = "Create {} {} returned HTTP status {} {}".format(self.uri, method, response.status_code, response.reason)
            raise ResourceError(self.uri, self.repo.user, response, message)


    def _ensure_rdf_type(self):
        """Make sure that this Resource has an RDF.type triple specified
        by its class"""

        if not self.RDF_TYPE:
            return
        if self.uri:
            s = URIRef(self.uri)
        else:
            s = URIRef('')
        type_triple = ( s, RDF.type, self.RDF_TYPE )
        self.repo.logger.warning(type_triple)
        ts = self.rdf.triples(type_triple)
        self.repo.logger.warning(ts)
        if not next(ts, None):
            self.rdf.add(type_triple)
        else:
            self.repo.logger.warning("Didn't add type")


    def add(self, resource, slug=None, path=None, force=False):
        """Add a new Resource object as a child of this Resource"""
        return resource.create(self.uri, slug=slug, path=path, force=force) 
            

    def add_container(self, metadata, slug=None, path=None, force=False):
        """Add a new container to this resource.

        Parameters:
        metadata ([ (p, o) ]) -- a list of ( predicate, object ) tuples
        path (str) -- path to new container, relative to uri
        slug (str) -- slug of new container
        force (boolean) -- where path is used, whether to force an overwrite

        Using the path parameter will try to create a deterministic path. If
        the path already exists and force is False (the default), an error is
        raised. If the path already exists and force is True, the existing
        path is deleted and obliterated and a new, empty container is created.

        """
        resourceClass = typedResource(metadata)
        resource = resourceClass(self.repo)
        return resource.create(self.uri, metadata=metadata, slug=slug, path=path, force=force)


        
    def add_binary(self, source, slug=None, path=None, force=False, mime=None):
        """Add a new binary object to this resource.

        Parameters:
        source (str or file-like) -- an IO-style object, URI or filename
        path (str) -- path to new container, relative to uri
        slug (str) -- slug of new container
        force (boolean) -- where path is used, whether to force an overwrite

        The path, slug and force parameters have the same meaning as for
        add_container
        
        """
        binary = Binary(self)
        return binary.create(uri, source, slug=slug, path=path, force=force, mime=mime)

    



    def put(self):
        """Put the Resource to the repository, using force. Used when
        writing Auths and other specialised resources.

        FIXME replace this with a call to the newer write"""
        

        self.repo._ensure_path(self.uri, True)
        rdf_text = self.rdf.serialize(format=RDF_MIME)
        headers = { 'Content-Type': RDF_MIME }
        response = self.repo.api(self.uri, method='PUT', headers=headers, data=rdf_text)
        if response.status_code == requests.codes.no_content:
            return self
        elif response.status_code == requests.codes.created:
            return self
        else:
            message = "put RDF {} returned HTTP status {} {}".format(self.uri, response.status_code, response.reason)
            raise ResourceError(self.uri, self.repo.user, response, message)



    def children(self):
        """Returns a list of paths of this resource's FEDORA children"""
        return self.rdf.objects(subject=URIRef(self.uri), predicate=LDP_CONTAINS)

    def rdf_types(self):
        """Returns a list of all this object's RDF.type values"""
        return self.rdf_get_all(RDF.type)

    def rdf_search(self, predfilter):
        """Returns a list of all the objects where predfilter(p) is true"""
        pos = self.rdf.predicates_objects(subject=URIRef(self.uri))
        return [ o for (p, o) in pos if predfilter(p) ]

    def rdf_get_all(self, predicate):
        """Returns a list of all the objects with a predicate """
        return list(self.rdf.objects(subject=URIRef(self.uri), predicate=predicate))

    def rdf_get(self, predicate):
        """Gets only one of the objects from rdf_get_all"""
        os = self.rdf_get_all(predicate)
        self.repo.logger.debug("List of all with predicate {}:{}".format(predicate, os))
        if os:
            return os[0]
        else:
            return None

    # Both rdf_add and rdf_set now build a list of RDF changes which
    # aren't applied until rdf_write is called. This is so that the module
    # can manage Fedora's requirements about RDF consistency w/r/t system
    # triples.
        
    def rdf_add(self, p, o):
        """Adds an RDF change to the stack to be written with rdf_write.

        Parameters:
        p (URIRef) - the RDF predicate
        o (Literal or URIRef) - the property or value

        Changes made with rdf_add will be added - existing triples with
        predicate p will not be overwritten.  To replace a predicate use
        rdf_replace.

        """
        self.changes.append((RDF_ADD, p, o))

    def rdf_replace(self, p, o):
        """Adds an RDF change to the stack to be written with rdf_write.

        Parameters:
        p (URIRef) - the RDF predicate
        o (Literal or URIRef) - the property or value

        Changes made with rdf_replace will overwrite all existing triples
        with predicate p.  To add a triple without removing existing triples,
        use rdf_add
        """        
        self.changes.append((RDF_REPLACE, p, o))

    def rdf_remove(self, p):
        """Adds an RDF change to the stack to be written with rdf_write.

        Parameters:
        p (URIRef) - the RDF predicate

        Removes all triples with the predicate p from the RDF graph when
        rdf_write is called.

        """        
        self.changes.append((RDF_REMOVE, p, None))



    def rdf_read(self):
        """Read the metadata from Fedora"""
    
        most_recent = self.repo.get(self.uri, headers={ 'Accept': RDF_MIME })
        self.rdf = most_recent.rdf
        return self.rdf
    
    def rdf_write(self):
        """Updates a resource's metadata, based on the list of changes
        which has been build by calls to rdf_add, rdf_replace and rdf_remove.
        """
        
        if not self.rdf:
            raise Error("Resource at uri {} is not an RDF-resource".format(self.uri))
        if not self.changes:
            self.repo.logger.error("Call to rdf_write before any changes specified")
            raise Error("No changes for rdf_write on {}".format(self.uri))
            return None
        
        # Make sure that the resource has a current set of RDF         
        
        self.rdf_read()

        with open('dump-before.turtle', 'wb') as tf:
            tf.write(self.rdf.serialize(format=RDF_MIME))
        self.repo.logger.debug("Change list = {}".format(self.changes))
        
        for ( t, p, o ) in self.changes:
            self.repo.logger.debug("Change: {} {} {}".format(t, p, o))
            if t == RDF_REPLACE or t == RDF_REMOVE:
                self.rdf.remove((URIRef(self.uri), p, None))
            if t == RDF_REPLACE or t == RDF_ADD:
                self.rdf.add((URIRef(self.uri), p, o))

        rdf = self.rdf.serialize(format=RDF_MIME)
        with open('dump-after.turtle', 'wb') as tf:
            tf.write(rdf)
        headers = { 'Content-type': RDF_MIME }
        # FIXME: replace this with write()
        response = self.repo.api(self.uri, method='PUT', headers=headers, data=rdf)
        if response.status_code == requests.codes.no_content:
            return self
        else:
            message = "put RDF {} returned HTTP status {} {}".format(self.uri, response.status_code, response.reason)
            raise ResourceError(self.uri, self.repo.user, response, message)


        
