#!/usr/bin/env python

import requests, json, re, sys

from rdflib import Graph, Literal, URIRef, Namespace, RDF
from rdflib.namespace import DC

import fc4

fcurl = 'http://localhost:8080/fcrepo'
user = 'fedoraAdmin'
password = 'secret3'

repo = fc4.Repository(fcurl, user, password)





#with open('body.rdf') as frdf:
#    rdf = frdf.read()

print("RDF:\n====\n{}\n====".format(rdf))

response = repo.new_container('test_push', rdf, 'text/turtle')

if not response.status_code == requests.codes.created:
    print("Request failed: {}".format(response.status_code))
    sys.exit(-1)
    
container = path = response.text



#container = 'test_push/65/7f/94/3c/657f943c-9095-4a56-be61-e919488fa1a8'



response = repo.get(container)

if response.status_code == requests.codes.ok:
    print("Get request returned OK status")
else:
    sys.exit(-1)


acl = repo.get_access(container)

print("ACL for {}".format(container))
print(acl)

repo.set_access(container, { 'admin': [ 'admin' ] })

acl = repo.get_access(container)

print("ACL for {}".format(container))
print(acl)
