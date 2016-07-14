import requests, os.path, mimetypes
from urllib.parse import urlparse

from fcrepo4.resource import Resource, resource_register

DEFAULT_MIME_TYPE = 'application/octet-stream'
URL_CHUNK_SIZE = 1024


class Binary(Resource):
    """Class representing a binary, non-RDF resource"""

    RDF_TYPE = None

    def create(self, container, source=None, metadata=None, slug=None, basename=False, path=None, force=None, mime=DEFAULT_MIME_TYPE):
        """Create a Binary in the repository. Note that metadata here is not
        an rdf Graph but a dict, because in Fedora binary objects don't have
        RDF metadata. Also note that *metadata is not implemented yet*

        source can be one of:

        * a URL: in which case, the binary will be streamed from that URL
        * a string which doesn't look like a URL: interpreted as a filename
        * a file-like object

        URLs and files have a 'natural' slug - the basename of the path

            binary.create(source=url) -> gets a Fedora path
            binary.create(source=url, slug="custom_slug")  -> tries this_file.jpg
            binary.create(source=url, basename=True) -> use the basename as a slug
        
        
        """

        if type(container) == str:
            self.target_uri = container
        else:
            self.target_uri = container.uri
        if path:
            self.method = 'PUT'
            self.target_uri = self.repo.pathconcat(self.target_uri, path)
        else:
            self.method = 'POST'
        self.force = force
        self.source = source
        self.use_basename = basename
        self.slug = slug
        self.mime = mime
        if type(self.source) == str:
            if self._is_url(source):
                return self._create_from_url()
            else:
                return self._create_from_filename()
        else:
            return self._create_from_filehandle()


    def _is_url(self, source):
        """Tries to parse a data source string as a URL. If the result is
        a http or https URL, returns True.
        """
        p = urlparse(source)
        return p.scheme == 'http' or p.scheme == 'https'

    def _make_headers(self):
        """Builds HTTP headers"""
        headers = { 'Content-Type': self.mime }
        if self.basename and self.use_basename:
            headers['Content-Disposition'] = 'attachment; filename="{}"'.format(self.basename)
        if self.slug:
            headers['Slug'] = self.slug
        return headers

    def _create_from_filename(self):
        """Create a binary from a filename"""
        self.basename = os.path.basename(self.source)
        self.mime, _ = mimetypes.guess_type(self.source)
        headers = self._make_headers()
        with open(self.source, 'rb') as fh:
            if self.method == 'PUT':
                self.repo._ensure_path(self.target_uri, self.force)
            return self._create_api(self.target_uri, self.method, headers, fh)


    def _create_from_filehandle(self):
        """Create a binary from a file-like object"""
        self.basename = None
        headers = self._make_headers()
        if self.method == 'PUT':
            self.repo._ensure_path(self.target_uri, self.force)
        return self._create_api(self.target_uri, self.method, headers, self.source)
            
            
    def _create_from_url(self):
        """Create a binary from a url.
        
        Open the source URL as a stream, then use the requests method
        iter_content to get a generator
        see http://docs.python-requests.org/en/master/user/advanced/
        """
        response = requests.get(self.source, stream=True)
        self.mime = response.headers['Content-type']
        self.basename = self.source.split('/')[-1]
        headers = self._make_headers()
        if self.method == 'PUT':
            self.repo._ensure_path(self.target_uri, self.force)
        return self._create_api(self.target_uri, self.method, headers, response.iter_content(URL_CHUNK_SIZE))

    


