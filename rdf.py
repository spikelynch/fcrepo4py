#!/usr/bin/env python3

# let's create some RDF

from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF

print(DC.title)
print(DC.format)
print(DC['format'])
