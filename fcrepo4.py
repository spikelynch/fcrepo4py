"""
A Pythonic interface to Fedora Commons 4

Repository - connection to an FCREPO

Resource -> path
         -> status (tombstones etc)
         -> access
         -> triples (RDF metadata)
         -> children (list of child resources)
         -> content (bytes)

r = repo.get(path)

for c in r.children:
    

"""

import requests, os.path, mimetypes, json, yaml, logging, re
from urllib.parse import urlparse
from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC
import types


logging.basicConfig(format="[%(name)s] %(levelname)s: %(message)s")

METHODS = {
    'GET': requests.get,
    'PUT': requests.put,
    'POST': requests.post,
    'PATCH': requests.patch,
    'DELETE': requests.delete,
    'HEAD': requests.head,
    'OPTIONS': requests.options,
#    'MOVE': requests.move,
#    'COPY': requests.copy
}

# the following are what the code uses as a serialisation format for
# RDF between the repository and the Resource objects: the first is
# the mime type requested of the server, the second is the rdflib parser
    
RDF_MIME = 'text/turtle'
RDF_PARSE = 'turtle'    

FC4_URL = 'http://fedora.info/definitions/v4/repository#'

FC4_NS = Namespace(FC4_URL)
FC4_LAST_MODIFIED = FC4_NS['lastModified']

LDP_CONTAINS = 'http://www.w3.org/ns/ldp#contains'

WEBAC_URL = 'http://www.w3.org/ns/auth/acl#'

WEBAC_NS = Namespace(WEBAC_URL)

READ = WEBAC_NS['Read']
WRITE = WEBAC_NS['Write']

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

LOGLEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
    }

URL_CHUNK = 512

RDF_ADD = 0
RDF_REPLACE = 1
RDF_REMOVE = 2

FCR_ACCESS = 'fcr:accessroles'

class Error(Exception):
    """Base class for exceptions.

    Attributes:
        message (str): the error message"""

    def __init__(self, message):
        self.message = message

        
class URIError(Error):
    """Error for malformed URIs.

    Attributes:
        message (str)
    """
    pass

class ConflictError(Error):
    """Error for conflicts: like trying to create a path which exists"""
    pass

class ResourceError(Error):
    """Base class for API/Resource errors.

    Attributes:
        uri (str) -- the uri of the resource
        user (str) -- the user who attempted the request
        response (requests.Response) -- the HTTP response
        status_code (int) -- the HTTP status returned by the request
        reason (str) -- the text version of the HTTP status code
        message (str) -- an error messsage
"""

    def __init__(self, uri, user, response, message):
        """Parameters:

        uri (str): the uri of the resource
        user (str): the user who made the request
        response (requests.Response): the HTTP response
        message (str): additional message from the code throwing the exception
        """
        self.uri = uri
        self.user = user
        self.response = response
        self.status_code = response.status_code
        self.reason = response.reason
        self.message = message



class Repository(object):
    """Object representing a FC4 repository and associated config values
       like usernames and passwords.
    """
    
    def __init__(self, config='config.yml', user='user', loglevel=logging.WARNING):
        """"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(loglevel)
        configd = {}
        if type(config) == dict:
            self.logger.debug("config is a dict")
            configd = config
        else:
            configd = self.load_config(config)
        fields = [ 'uri', 'users' ]
        m = [ f for f in fields if f not in configd ]
        if m:
            message = "Config values missing: {}".format(', '.join(m))
            self.logger.critical(message)
            raise Error(message)
        if 'loglevel' in configd:
            if configd['loglevel'] in LOGLEVELS:
                self.logger.setLevel(LOGLEVELS[configd['loglevel']])
                self.logger.info("Log level set to '{}' by {}".format(configd['loglevel'], config))
            else:
                self.logger.error("Warning: config {} matches no log level".format(configd['loglevel']))
        self.logger.debug("Config = {}".format(configd))
        self.uri = configd['uri']
        self.users = configd['users']
        if 'rdfdump' in configd:
            self.rdfdump = configd['rdfdump']
            self.logger.debug("Dumping rdf to {}".format(self.rdfdump))
        else:
            self.rdfdump = None
        self.set_user(user)
        if self.uri[-1:] != '/':
            self.uri += '/'
        self.pathre = re.compile("^{}rest/(.*)$".format(self.uri))


    def set_user(self, user):
        if user in self.users:
            self.user = self.users[user]['user']
            self.password = self.users[user]['password']
        else:
            message = "Couldn't find user '{}' in config".format(user)
            self.logger.error(message)
            raise Error(message)

        
    def load_config(self, conffile):
        cf = None
        message = ''
        with open(conffile) as cf:
            try:
                cf = yaml.load(cf)
            except yaml.YAMLError as exc:
                message = "YAML {} parse error: {}".format(conffile, exc)
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    message += "Error position: {}:{}".format(mark.line + 1, mark.column + 1)
        if not cf:
            self.logger.critical(message)
            raise Error(message)
        return cf

    def path2uri(self, path):
        """Converts a REST API path to an absolute url"""
        uri = self.uri + 'rest'
        if not path:
            return uri
        if path[0] != '/':
            return uri + '/' + path
        return uri + path

    def path2reluri(self, path):
        """Converts a REST API path to a relative url"""
        uri = '/rest'
        if not path:
            return uri
        if path[0] != '/':
            return uri + '/' + path
        return uri + path

    
    def uri2path(self, uri):
        """Converts a full uri to a REST path.

Throws an exception if the uri doesn't match this repository
"""
        m = self.pathre.match(uri)
        if m:
            return m.group(1)
        else:
            raise URIError("Path mismatch - couldn't parse {} to a path in {}".format(uri, self.uri))
        
        
    def api(self, uri, method='GET', headers=None, data=None, auth=None):
        """
Generic api call with an HTTP method, target URL and headers, data (for
plain POST) or files (for file uploads)

Default method is GET.
"""
        self.uri2path(uri)  # safety check: throw URI error if it's bad
        if method in METHODS:
            m = METHODS[method]
            self.logger.debug("API {} {}".format(method, uri))
            if headers:
                self.logger.debug("headers={}".format(headers))
            self.logger.debug("Authentication: {} {}".format(self.user, self.password))
            r = m(uri, auth=(self.user, self.password), headers=headers, data=data)
            return r
        else:
            return None

    def pathconcat(self, path, s):
        """Appends a suffix like fc:tombstone to a path"""
        if path[:-1] == '/':
            return path + s
        else:
            return path + '/' + s

    def dc_rdf(self, md):
        """A utility method for building a DC RDF graph from a dict"""
        g = Graph()

        obj = URIRef("")

        for field in DC_FIELDS:
            if field in md:
                g.add( (obj, DC[field], Literal(md[field])) )
        g.bind("dc", DC)
        return g

    def build_rdf(self, metadata, bind=None):
        """Takes a set of tuples and builds an RDF Graph object."""

        g = Graph()
        obj = URIRef("")
        for ( p, o ) in metadata:
            g.add((obj, p, o))
        if bind:
            for abbrev, namespace in bind.items():
                g.bind(abbrev, namespace)
        return g
        
    def get(self, uri, headers=None):
        """The basic method for retrieving a resource.

        Fetches the metadata for the resource at uri, raises a ResourceError
        if the status code was something other than ok
        """

        if headers:
            response = self.api(uri, headers=headers)
        else:
            response = self.api(uri)
        if response.status_code == requests.codes.ok:
            resource = Resource(self, uri, response=response)
            if response.headers['Content-type'] == 'text/turtle':
                resource._parse_rdf(response.text)
            return resource
        else:
            message = "get {} returned HTTP status {} {}".format(uri, response.status_code, response.reason)
            raise ResourceError(uri, self.user, response, message)



    def add_container(self, uri, metadata, slug=None, path=None, force=False):
        """Add a new container inside an existing one.

        Parameters:
        uri (str) -- the path of the container to add to
        metadata (Graph) -- the RDF 
        path (str) -- path to new container, relative to uri
        slug (str) -- slug of new container
        force (boolean) -- where path is used, whether to force an overwrite

        Using the path parameter will try to create a deterministic path. If
        the path already exists and force is False (the default), a
        ConflictError is raised. If the path already exists and force is True,
        the existing path is deleted and obliterated and a new container is
        created.

        """
        rdf = metadata.serialize(format=RDF_MIME)
        headers = { 'Content-Type': RDF_MIME }
        if path:
            method = 'PUT'
            uri = self.pathconcat(uri, path)
            self._ensure_path(uri, force)
        else:
            method = 'POST'
            if slug:
                headers['Slug'] = slug
        resource = self._add_resource(uri, method, headers, rdf)
        #self.logger.debug(rdf)
        resource.rdf = metadata
        return resource


    def add_acl(self, uri, path="acl", force=False):
        """Add a new container and make it an ACL

        Parameters:
        uri (str) -- the path of the container to add to
        path (str) -- path to new container, relative to uri
        force (boolean) -- where path is used, whether to force an overwrite

        The acl will be created with a preset path, and RDF setting the ACL's
        type.
        """
        rdf = Graph()
        this = URIRef('')
        rdf.add( ( this, RDF.type, WEBAC_NS['Acl']) )
        rdf_text = rdf.serialize(format=RDF_MIME)
        headers = { 'Content-Type': RDF_MIME }
        method = 'PUT'
        uri = self.pathconcat(uri, path)
        self._ensure_path(uri, force)
        if self._add_resource(uri, method, headers, rdf_text):
            acl = Acl(self, uri)
            acl.rdf = rdf
            return acl
        return None

    
    def add_binary(self, uri, source, slug=None, path=None, force=None, mime=None):
        """Upload binary data to a container.

        Parameters
        uri (str) -- the path of the container at which to add it
        metadata (Graph) -- RDF
        source (str, URI, file-like, generator) -- a filename, URI or stream
        mime (str) -- MIME type
        basename (str) -- 
        slug (str) -- preferred id
        path (str) -- relative path from uri
        force (boolean) -- whether to overwrite path if it exists

        If no value is provided for path or slug, this method will try to
        use one from the filename or URI if possible: if not, it will let
        Fedora generate one.

        If a MIME-type is not provided, it's guessed from the filename, or
        taken from the URI. When passing in any other type of stream-like
        object, you should specify the MIME type: it will default to
        'application/octet-stream' otherwise. 
        """
        headers = {  }
        if path:
            method = 'PUT'
            uri = self.pathconcat(uri, path)
            self._ensure_path(uri, force)
            self.logger.debug("PUTting binary to {}".format(uri))
        else:
            method = 'POST'
            if slug:
                headers['Slug'] = slug
            self.logger.debug("POSTing binary to {} {}".format(uri, slug))

            
        if type(source) == str:
            if self._is_url(source):
                # open the source URL as a stream, then use the requests method
                # iter_content to get a generator which we pass to _add_resource
                # see http://docs.python-requests.org/en/master/user/advanced/
                source_r = requests.get(source, stream=True)
                headers['Content-type'] = source_r.headers['Content-type']
                basename = source.split('/')[-1]
                if method == 'POST' and slug:
                    basename = slug
                headers['Content-Disposition'] = 'attachment; filename="{}"'.format(basename)
                return self._add_resource(uri, method, headers, source_r.iter_content(URL_CHUNK))
                
            else:
                basename = os.path.basename(source)
                headers['Content-type'], _ = mimetypes.guess_type(source)
                headers['Content-Disposition'] = 'attachment; filename="{}"'.format(basename)
                with open(source, 'rb') as fh:
                    resource = self._add_resource(uri, method, headers, fh)
                return resource
        else: # let's assume it's a file-like thing
            if mime:
                headers['Content-type'] = mime
            if slug:
                headers['Content-Disposition'] = 'attachment; filename="{}"'.format(slug)
            resource = self._add_resource(uri, method, headers, source)
            return resource

    def _is_url(self, source):
        """Tries to parse a data source string as a URL. If the result is
        a http or https URL, returns True.
        """
        p = urlparse(source)
        return p.scheme == 'http' or p.scheme == 'https'

        
    def _add_resource(self, uri, method, headers, data):
        """Internal method for PUT/POST: this does the error handling and
        builds the returned Resource object
        """
        self._rdf_dump(data, uri)
        response = self.api(uri, method=method, headers=headers, data=data)
        if response.status_code == requests.codes.created:
            uri = response.text
            return Resource(self, uri)
        else:
            message = "{} {} failed: {} {}".format(method, uri, response.status_code, response.reason)
            self.logger.error(message)            
            raise ResourceError(uri, self.user, response, message) 


    def _rdf_dump(self, data, uri):
        if self.rdfdump:
            try:
                uri_path = uri.replace('/', '_')
                dumpf = os.path.join(self.rdfdump, uri_path) + '.ttl'
                with open(dumpf, 'wb') as df:
                    self.logger.debug("Dumping RDF to {}".format(dumpf))
                    df.write(data)
            except TypeError as te:
                pass   # this catches errors when data is not a bytes-like


        
    def _ensure_path(self, path, force):
        """Internal method to check if a path is free (and make sure it is
        if force is True. - this currently breaks if it's applied to a
        non-RDF path
        """
        response = None
        try:
            response = self.api(path)
        except ResourceError as re:
            if re.status_code == requests.codes.not_found:
                # not found is good
                self.logger.debug("Checked for {} - not found".format(path))
                pass
            else:
                raise re
        if response:
            if force:
                self.logger.debug("Force: obliterating {}".format(path))
                self.delete(path)
                self.obliterate(path)
            else:
                message = "Path {} already exists: can't re-create without force".format(path)
                self.logger.error(message)
                raise ConflictError(message)
    

        
    # def _handle_data(self, source):
    #     """Take the data source passed to the add_binary function and turn it
    #     into a stream-like thing, if it isn't one.

    #     Parameters:
    #     source (str or file-like thing)

    #     Returns:
    #     a triple of ( mimetype (str), base name (str), stream (stream) )
    #     """


    



        


    

    def delete(self, uri):
        """Deletes a resource"""
        return self._delete_uri(uri)

    def obliterate(self, uri):
        """Removes the tombstone record left by a resource"""
        tombstone = self.pathconcat(uri, 'fcr:tombstone')
        return self._delete_uri(tombstone)

    def _delete_uri(self, uri):
        response = self.api(uri, method="DELETE")
        if response.status_code == requests.codes.no_content:
            return True
        else:
            message = "delete {} returned HTTP status {} {}".format(uri, response.status_code, response.reason)
            raise ResourceError(uri, self.user, response, message)



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

    def bytes(self):
        """TBD - stream the resources' bytes"""
        pass

    def children(self):
        """Returns a list of paths of this resource's FEDORA children"""
        return self.rdf.objects((URIRef(self.uri), LDP_CONTAINS, None))

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
        for field in DC_FIELDS:
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
        
    def add_binary(self, source, slug=None, path=None, force=False):
        """Add a new binary object to this resource.

        Parameters:
        source (str or file-like) -- an IO-style object, URI or filename
        path (str) -- path to new container, relative to uri
        slug (str) -- slug of new container
        force (boolean) -- where path is used, whether to force an overwrite

        The path, slug and force parameters have the same meaning as for
        add_container
        
        """
        return self.repo.add_binary(self.uri, source, slug=slug, path=path, force=force)

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
        response = self.repo.api(self.uri, method='PUT', headers=headers, data=rdf)
        if response.status_code == requests.codes.no_content:
            return self
        else:
            message = "put RDF {} returned HTTP status {} {}".format(self.uri, response.status_code, response.reason)
            raise ResourceError(self.uri, self.repo.user, response, message)



class Acl(Resource):
    """Class representing a Web AC ACL"""
    
    def grant(self, path, user, access, uri):
        """Grant a user an access level over a resource, specified by its
        URI.  The authorisation has to be given a path relative
        to the ACL: existing authorisations with this path will be overwritten.
        Also adds a triple to the resource at uri pointing to this ACL
        as its access source
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
                
        rdf = Graph()
        rdf.bind('acl', WEBAC_NS)
        this = URIRef('')
        rdf.add( ( this, RDF.type, WEBAC_NS['Authorization']) )
        rdf.add( ( this, WEBAC_NS['accessTo'], URIRef(uri) ) )
        rdf.add( ( this, WEBAC_NS['mode'],     access ) )
        rdf.add( ( this, WEBAC_NS['agent'],    Literal(user) ) )
        
        auth = self.add_container(rdf, path=path, force=True)

            
        

    def remove(self, path):
        uri = self.repo.pathconcat(self.uri, path)
        self.repo.delete(uri)
        self.repo.obliterate(uri)
