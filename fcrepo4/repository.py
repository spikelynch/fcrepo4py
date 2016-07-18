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

import requests, os.path, mimetypes, json, yaml, logging, re, sys
from urllib.parse import urlparse
from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC
import types

from fcrepo4.resource import Resource, Binary, typedResource
from fcrepo4.resource.webac import Acl

from fcrepo4.exception import Error, ResourceError, ConflictError, URIError

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



FC4_URL = 'http://fedora.info/definitions/v4/repository#'

FC4_NS = Namespace(FC4_URL)
FC4_LAST_MODIFIED = FC4_NS['lastModified']


WEBAC_URL = 'http://www.w3.org/ns/auth/acl#'

WEBAC_NS = Namespace(WEBAC_URL)


RDF_MIME = 'text/turtle'
RDF_PARSE = 'turtle'    


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



FCR_ACCESS = 'fcr:accessroles'


class Repository(object):
    """Object representing a FC4 repository and associated config values
       like usernames and passwords.
    """
    
    def __init__(self, config='config.yml', user='user', loglevel=logging.WARNING):
        """Creator"""
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
                self.logger.debug("Log level set to '{}' by {}".format(configd['loglevel'], config))
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
        if 'delegated' in configd:
            self.delegated = bool(configd['delegated'])
        else:
            self.delegated = False
        self.set_user(user)
        if self.uri[-1:] != '/':
            self.uri += '/'
        self.pathre = re.compile("^{}rest/(.*)$".format(self.uri))
        self.cf = configd

        
    def set_user(self, user):
        """Sets the current user.

        Subsequent REST actions will be authenticated with this user's
        credentials. If the repo is in delegated mode, actions will be
        authenticated with the fedoraAdmin user and delegated to the current
        user with HTTP headers.
        """
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
        self.uri2path(uri)  # safety check: will throw an URI error if it's bad
        if method in METHODS:
            m = METHODS[method]
            self.logger.debug("API {} {}".format(method, uri))
            self.logger.debug("Authentication: {} {}".format(self.user, self.password))
            if self.delegated and self.user != 'fedoraAdmin':
                auth = ( self.users['fedoraAdmin']['user'], self.users['fedoraAdmin']['password'] )
                if not headers:
                    headers = {}
                headers['On-Behalf-Of'] = self.user
                self.logger.debug("Delegated authentication as {}".format(self.user))
            else:
                auth = (self.user, self.password)
            if headers:
                self.logger.debug("headers={}".format(headers))
            r = m(uri, auth=auth, headers=headers, data=data)
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

        Looks up the resource at uri. If the request is a success, creates
        a Resource object with the metadata and http response.

        If the request returned a not found error, returns None

        If the request returned any other kind of non-OK status, throws
        a ResourceError with the status code and reason.
        """

        if headers:
            response = self.api(uri, headers=headers)
        else:
            response = self.api(uri)
        if response.status_code == requests.codes.ok:
            if response.headers['Content-type'] == 'text/turtle':
                # if it has RDF, try to get the right class
                rdf = Graph()
                rdf.parse(data=response.text, format=RDF_PARSE)
                resourceclass = typedResource(rdf)
                return resourceclass(self, uri, metadata=rdf, response=response)
            else:
                # if it's not RDF then this should probably be a binary
                # but check
                return Resource(self, uri, response=response)
        elif response.status_code == requests.codes.not_found:
            return None
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
        resourceClass = typedResource(metadata)
        resource = resourceClass(self)
        return resource.create(uri, metadata=metadata, slug=slug, path=path, force=force)
        

    def add_acl(self, uri, path="acl", force=False):
        """Add a new container and make it an ACL

        Parameters:
        uri (str) -- the path of the container to add to
        path (str) -- path to new container, relative to uri
        force (boolean) -- where path is used, whether to force an overwrite

        The acl will be created with a preset path, and RDF setting the ACL's
        type.

        FIXME - this needs to be moved into the Resource class hierarchy
        
        """
        acl = Acl(self)
        return acl.create(uri, path=path, force=force)

    
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

        binary = Binary(self)
        return binary.create(uri, source, slug=slug, path=path, force=force, mime=mime)

        
        
    # def _add_resource(self, uri, method, headers, data):
    #     """Internal method for PUT/POST: this does the error handling and
    #     builds the returned Resource object
    #     """
    #     self.logger.error("DEATH TO _add_resource")
    #     sys.exit(-1)
    #     self._rdf_dump(data, uri)
    #     response = self.api(uri, method=method, headers=headers, data=data)
    #     if response.status_code == requests.codes.created:
    #         uri = response.text
    #         # FIXME: call a factory method on fcrepo4.resource which returns
    #         # an object of the correct kind
    #         return Resource(repo=self, uri=uri)
    #     else:
    #         message = "{} {} failed: {} {}".format(method, uri, response.status_code, response.reason)
    #         self.logger.error(message)            
    #         raise ResourceError(uri, self.user, response, message) 


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


