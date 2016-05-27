#!/usr/bin/env python

import requests, json, re, sys


import fc4

fcurl = 'http://localhost:8080/fcrepo'
user = 'fedoraAdmin'
password = 'secret3'

DATAFILE = '/Users/mike/Desktop/Fedora4/Develop/burd.jpg'

repo = fc4.Repository(fcurl, user, password)

g = Graph()

obj = URIRef("")

g.add( (obj, DC.title, Literal("Container title")) )
g.add( (obj, DC.description, Literal("This is a container added from a python script")) )
g.add( (obj, DC.creator, Literal("Mike Lynch")) )

g.bind("dc", DC)

rdf = g.serialize(format='text/turtle')

#with open('body.rdf') as frdf:
#    rdf = frdf.read()

print("RDF:\n====\n{}\n====".format(rdf))

response = repo.new_container('test_push', rdf, 'text/turtle')

if not response.status_code == requests.codes.created:
    print("Request failed: {}".format(response.status_code))
    sys.exit(-1)
    
container = path = response.text


getpath = re.compile("^" + fcurl + "/rest/(.*)")

m = getpath.match(path)

if not m:
    print("Couldn't grep path from URL")
    sys.exit(-1)

path = m.group(1)

print("New container added at {}".format(path))


response = repo.get(path)

if response.status_code == requests.codes.ok:
    print("Get request returned OK status")
    print("Response:\n{}".format(response.text))
else:
    sys.exit(-1)

response = repo.add_file(path, DATAFILE)

print(response.status_code)
print(response.text)

acl = repo.get_access(container)

print("ACL for {}".format(container))
print(acl)

repo.set_access(container, { 'admin': [ 'admin' ] })

acl = repo.get_access(container)

print("ACL for {}".format(container))
print(acl)
