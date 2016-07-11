#!/usr/bin/env python

import logging, argparse
from rdflib import Literal, URIRef

from rdflib.namespace import DC

from fcrepo4 import Repository
#from fcrepo4.resource import Resource
   

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('uri', type=str, help="A Fedora URI")
    parser.add_argument('-c', '--config', default="config.yml", type=str, help="Config file")
    args = parser.parse_args()
    repo = Repository(config=args.config)
    repo.set_user('fedoraAdmin')
    resource = repo.get(args.uri)
    if resource:
        print(resource.rdf.serialize(format='text/turtle'))
    else:
        print("URI {} not found".format(args.uri))
