import requests
from fcrepo4.resource import Resource, resource_register

DEFAULT_MIME_TYPE = 'application/octet-stream'


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

        data = None
        bname = None
        if type(source) == str:
            if self._is_url(source):
                mime, bname, source = self._data_from_url(source)
            else:
                mime, bname, source = self._data_from_file(source)
        headers = { 'Content-Type': mime }
        if bname:
            headers['Content-Disposition'] = 'attachment; filename="{}"'.format(bname)
        if path:
            method = 'PUT'
            uri = self.repo.pathconcat(uri, path)
            self.repo._ensure_path(uri, force)
        else:
            method = 'POST'
            if basename and bname:
                headers['Slug'] = bname
            elif slug:
                headers['Slug'] = slug

        return self._create_api(uri, method, headers, data)



    def _is_url(self, source):
        """Tries to parse a data source string as a URL. If the result is
        a http or https URL, returns True.
        """
        p = urlparse(source)
        return p.scheme == 'http' or p.scheme == 'https'


    def _data_from_filename(self, filename):
        basename = os.path.basename(source)
        mimetype, _ = mimetypes.guess_type(source)
        data = open(filename, 'rb')
        return mimetype, basename, data


    def _data_from_url(self, method, url):
        """Creates a binary from a url.
        
        Open the source URL as a stream, then use the requests method
        iter_content to get a generator
        see http://docs.python-requests.org/en/master/user/advanced/
        """
        source_r = requests.get(source, stream=True)
        mimetype = source_r.headers['Content-type']
        basename = source.split('/')[-1]
        return mimetype, basename, source_r.iter_content(URL_CHUNK)


