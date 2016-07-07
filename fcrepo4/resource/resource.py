#import requests, os.path, mimetypes, json, yaml, logging, re
#from urllib.parse import urlparse

import fcrepo4

from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC


RDF_ADD = 0
RDF_REPLACE = 1
RDF_REMOVE = 2


class Resource(object):
    """Object representing a resource.

Attributes
    repo (Repository): the repository
    uri (str): its URI
    rdf (Graph): its RDF graph
    response (Response): the requests.Response object, if available

The methods on Resource objects mostly pass through to the corresponding
methods on its Repository object.
    """

    def __init__(self, repo, uri, metadata=None, response=None):
        """
Create a new Resource. Shouldn't be used by calling code - use the get and
children methods for that.

If the Resource was created by an http request, the requests.Response object
is stored (as 'response')
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

    def check_type(self):
        """See if this resource's RDF indicates that it should be one of the
        specialised subclasses like Acl"""

        if not self.rdf:
            return self
        ts = self.rdf_get_all(RDF.type)
        newclass = None
        if WEBAC_NS['Acl'] in ts:
            newclass = Acl
        elif WEBAC_NS['Authorization'] in ts:
            newclass = Auth
        if newclass:
            return newclass(self.repo, self.uri, metadata=self.rdf, response=self.response)
        return self

        
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

    def put(self):
        """Put the Resource to the repository, using force. Used when
        writing Auths and other specialised resources."""

        self.repo._ensure_path(self.uri, True)
        rdf_text = self.rdf.serialize(format=fcrepo4.RDF_MIME)
        headers = { 'Content-Type': fcrepo4.RDF_MIME }
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


    def dc(self):
        """Extracts all DC values and returns a dict"""
        dc = {}
        for field in fcrepo4.DC_FIELDS:
            value = self.rdf_get(DC[field])
            if value:
                dc[field] = str(value)
        return dc

        
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
        return self.repo.add_container(self.uri, metadata, slug=slug, path=path, force=force)
        
    def add_binary(self, source, slug=None, path=None, force=False, mime=DEFAULT_MIME_TYPE):
        """Add a new binary object to this resource.

        Parameters:
        source (str or file-like) -- an IO-style object, URI or filename
        path (str) -- path to new container, relative to uri
        slug (str) -- slug of new container
        force (boolean) -- where path is used, whether to force an overwrite

        The path, slug and force parameters have the same meaning as for
        add_container
        
        """
        return self.repo.add_binary(self.uri, source, slug=slug, path=path, force=force, mime=mime)

    def rdf_read(self):
        """Read the metadata from Fedora"""
    
        most_recent = self.repo.get(self.uri, headers={ 'Accept': fcrepo4.RDF_MIME })
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
            tf.write(self.rdf.serialize(format=fcrepo4.RDF_MIME))
        self.repo.logger.debug("Change list = {}".format(self.changes))
        
        for ( t, p, o ) in self.changes:
            self.repo.logger.debug("Change: {} {} {}".format(t, p, o))
            if t == RDF_REPLACE or t == RDF_REMOVE:
                self.rdf.remove((URIRef(self.uri), p, None))
            if t == RDF_REPLACE or t == RDF_ADD:
                self.rdf.add((URIRef(self.uri), p, o))

        rdf = self.rdf.serialize(format=fcrepo4.RDF_MIME)
        with open('dump-after.turtle', 'wb') as tf:
            tf.write(rdf)
        headers = { 'Content-type': fcrepo4.RDF_MIME }
        response = self.repo.api(self.uri, method='PUT', headers=headers, data=rdf)
        if response.status_code == requests.codes.no_content:
            return self
        else:
            message = "put RDF {} returned HTTP status {} {}".format(self.uri, response.status_code, response.reason)
            raise ResourceError(self.uri, self.repo.user, response, message)

