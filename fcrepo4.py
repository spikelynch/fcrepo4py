"""
Python objects for interacting with Fedora Commons 4 via its web API
"""

import requests, os.path, mimetypes, json

from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC

import logging

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

class FCRepository(object):
    """Connection to an FC4 repository."""
    
    def __init__(self, url, user, password, loglevel=logging.WARN):
        """Store the url, login and password"""
        self.url = url
        self.user = user
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(loglevel)


    def api(self, path, method='GET', headers=None, data=None):
        """
Generic api call with an HTTP method, target URL and headers, data (for
plain POST) or files (for file uploads)

Default method is GET.
"""
        url = self.url + '/rest/' + path
        if method in METHODS:
            m = METHODS[method]
            self.logger.debug("API {} {}".format(method, url))
            if headers:
                self.logger.debug("headers={}".format(headers))
            if data:
                self.logger.debug("data={}".format(data))
                with open("dump.rdf", "wb") as d:
                    d.write(data)
            r = m(url, auth=(self.user, self.password), headers=headers, data=data)
            return r
        else:
            return None


    def dc_rdf(self, title, description, creator):
        g = Graph()

        obj = URIRef("")

        g.add( (obj, DC.title, Literal(title)) )
        g.add( (obj, DC.description, Literal(description)) )
        g.add( (obj, DC.creator, Literal(creator)) )

        g.bind("dc", DC)
        return g.serialize(format='text/turtle')
    

        
    def get(self, path, format='application/ld+json'):
        response = self.api(path, headers={ 'Accept': format })
        return response
    
    def new_container(self, path, metadata):
        """Create a new container and return the response as JSON"""
        rdf = self.dc_rdf(metadata['title'], metadata['description'], metadata['creator'])
        response = self.api(path, method='PUT', headers={'Content-Type': 'text/turtle'}, data=rdf)
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
        response = self.api(path + '/fcr:accessroles')
        print(response.status_code)
        if response.status_code == requests.codes.ok:
            return json.loads(response.text)
        else:
            return "Bad status: {}".format(response.status_code)
            
    def set_access(self, path, acl):
        """Sets the access roles for the specified path"""
        response = self.api(path + '/fcr:accessroles', method='POST', headers={ 'Content-Type': 'application/json' }, data=json.dumps(acl))
        print("After set: {}".format(response.status_code))
