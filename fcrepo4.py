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

from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC

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

LDP_CONTAINS = 'http://www.w3.org/ns/ldp#contains'


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


class ResourceError(Error):
    """Base class for API/Resource errors.

    Attributes:
        uri (str) -- the uri of the resource
        status (int) -- the HTTP status returned by the request
        message (str) -- an error messsage
"""

    def __init__(self, uri, status, message):
        self.uri = uri
        self.status = status
        self.message = message



class Repository(object):
    """Connection to an FC4 repository."""
    
    def __init__(self, config='config.yml', loglevel=logging.WARN):
        """Store the uri, login and password"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(loglevel)
        configd = {}
        if type(config) == dict:
            self.logger.debug("config is a dict")
            configd = config
        else:
            configd = self.load_config(config)
        fields = [ 'uri', 'user', 'password' ]
        m = [ f for f in fields if f not in configd ]
        if m:
            message = "Config values missing: {}".format(', '.join(m))
            self.logger.critical(message)
            raise Error(message)
        
        self.uri = configd['uri']
        self.user = configd['user']
        self.password = configd['password']
        if self.uri[:-1] != '/':
            self.uri += '/'
        self.pathre = re.compile("^{}rest/(.*)$".format(self.uri))

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
        """Converts a REST API path to a url"""
        return self.uri + 'rest/' + path

    def uri2path(self, uri):
        """Converts a full uri to a REST path.

Throws an exception if the uri doesn't match this repository
"""
        m = self.pathre.match(uri)
        if m:
            return m.group(1)
        else:
            raise URIError("Path mismatch - couldn't parse {} to a path in {}".format(uri, self.uri))
        
        
    def api(self, path, method='GET', headers=None, data=None):
        """
Generic api call with an HTTP method, target URL and headers, data (for
plain POST) or files (for file uploads)

Default method is GET.
"""
        uri = self.path2uri(path)
        if method in METHODS:
            m = METHODS[method]
            self.logger.debug("API {} {}".format(method, uri))
            if headers:
                self.logger.debug("headers={}".format(headers))
            if data:
                self.logger.debug("data={}".format(data))
                with open("dump.rdf", "wb") as d:
                    d.write(data)
            r = m(uri, auth=(self.user, self.password), headers=headers, data=data)
            return r
        else:
            return None

    def suffix(self, path, s):
        """Appends a suffix like fc:tombstone to a path"""
        if path[:-1] == '/':
            return path + s
        else:
            return path + '/' + s

    def dc_rdf(self, title, description, creator):
        """A utility method for building a basic RDF graph with dc metadata"""
        g = Graph()

        obj = URIRef("")

        g.add( (obj, DC.title, Literal(title)) )
        g.add( (obj, DC.description, Literal(description)) )
        g.add( (obj, DC.creator, Literal(creator)) )

        g.bind("dc", DC)
        return g.serialize(format=RDF_MIME)
    

        
    def get(self, path):
        response = self.api(path, headers={ 'Accept': RDF_MIME })
        if response.status_code == requests.codes.ok:
            resource = Resource(self, path)
            resource._parse_rdf(response.text)
            return resource
        else:
            self.logger.error("get {} returned HTTP status {}".format(path, response.status_code))
            return None
    
    def new_container(self, path, metadata):
        """Create a new container and return the response as JSON"""
        rdf = self.dc_rdf(metadata['title'], metadata['description'], metadata['creator'])
        response = self.api(path, method='PUT', headers={'Content-Type': RDF_MIME}, data=rdf)
        return response

    def ensure_container(self, path, metadata):
        """Check to see if a path exists and create a container there if it doesn't"""
        response = self.get(path)
        if response.status_code == requests.codes.ok:
            # this should probably update the rdf
            print("path {} already exists found".format(path))
            return response
        print("path {} - trying to create".format(path))
        return self.new_container(path, metadata)
    
    def add_file(self, path, filename):
        """Add an object to a container"""

        basename = os.path.basename(filename)
        fh = open(filename, 'rb')
        mimetype = mimetypes.guess_type(filename)
        headers = {}
        headers['Content-Disposition'] = 'attachment; filename="{}"'.format(basename)
        headers['Content-Type'], _ = mimetype
        headers['Slug'] = basename
        print(headers)
        response = self.api(path, method='POST', headers=headers, data=fh)
        return response

    def get_access(self, path):
        """Gets the access roles for the specified path"""
        response = self.api(self.suffix(path, 'fcr:accessroles'))
        print(response.status_code)
        if response.status_code == requests.codes.ok:
            return json.loads(response.text)
        else:
            return "Bad status: {}".format(response.status_code)
            
    def set_access(self, path, acl):
        """Sets the access roles for the specified path"""
        response = self.api(self.suffix(path, 'fcr:accessroles'), method='POST', headers={ 'Content-Type': 'application/json' }, data=json.dumps(acl))
        print("After set: {}".format(response.status_code))


    def delete(self, path):
        """Deletes a resource"""
        response = self.api(path, method="DELETE")
        self.logger.debug(response.status_code)

    def obliterate(self, path):
        response = self.api(self.suffix(path, 'fcr:tombstone'), method="DELETE")
        self.logger.debug(response.status_code)
        



class Resource(object):
    """Object representing a resource.

Attributes
    repo (Repository): the repository
    path (str): its path (not URI)
    graph (Graph): its RDF graph
    """

    def __init__(self, repo, path):
        """
Create a new Resource. Shouldn't be used by calling code - use the get and
children methods for that
"""
        self.repo = repo
        self.path = path
        self.uri = self.repo.path2uri(self.path)
        
        
    def _parse_rdf(self, rdf):
        """Parse the serialised RDF content from FC as an rdflib Graph"""
        self.rdf = Graph()
        self.rdf.parse(data=rdf, format=RDF_PARSE)

    def bytes(self):
        """TBD - stream the resources' bytes"""
        pass

    def children(self):
        """Returns a list of paths of this resource's children"""
        self.children = [ o for (_, p, o) in self.rdf if p == LDP_CONTAINS ]
        return self.children
                
            
