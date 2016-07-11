from rdflib.namespace import Namespace

WEBAC_URL = 'http://www.w3.org/ns/auth/acl#'
WEBAC_NS = Namespace(WEBAC_URL)

READ = 'Read'
WRITE = 'Write'

from .acl import Acl
from .auth import Auth
