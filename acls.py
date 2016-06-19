#!/usr/bin/env python

import fcrepo4, logging
from rdflib import Literal, URIRef

from rdflib.namespace import DC

    



repo = fcrepo4.Repository(loglevel=logging.DEBUG)


repo.set_user('fedoraAdmin')

root = repo.get(repo.path2uri('/'))

mdt = repo.dc_rdf({'title': 'Testbed'})

c = root.add_container(mdt, path="acl_test_1", force=True)


acl = repo.add_acl(c.uri)

md = repo.dc_rdf({'title': 'My Container'})

resource = c.add_container(md, slug='my_container')

uri = resource.uri

acl.grant('autha', 'alice', fcrepo4.READ, uri)
acl.grant('authb1', 'bob', fcrepo4.READ, uri)
acl.grant('authb2', 'bob', fcrepo4.WRITE, uri)

        
try:
    repo.set_user('alice')
    r4 = repo.get(uri)
    md3 = repo.dc_rdf({'title': 'Alice added within'})
    r5 = r4.add_container(md3)
    print("Alice added child at {}".format(r5.uri))
except fcrepo4.ResourceError as e:
    print(e)


try:
    repo.set_user('bob')
    r2 = repo.get(uri)
    md2 = repo.dc_rdf({'title': 'Bob added within'})
    r3 = r2.add_container(md2)
    print("Bob added child at {}".format(r3.uri))
except fcrepo4.ResourceError as e:
    print(e)


