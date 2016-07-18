fcrepo4.py
==========

A simple Python 3 (not Python 2!) interface to Fedora Commons 4.

## Install

To install:
* Get yourself into a Python 3 virtual environment
* Get the library and install it:

    git clone https://codeine.research.uts.edu.au/eresearch/fcrepo4py.git

    cd fcrepo4py
  
    python setup.py install
  
## Usage

    from fcrepo.repository import Repository
    from fcrepo.resource import Resource, Binary

    # Connect to a repository

    repo = fcrepo4.Repository(config='config.yml)

    # Get the root container

    root = repo.get(repo.path2uri('/'))

    # Add a container to it (this will break if '/testbed' exists)

    c = root.add_container(path="testbed")

    # Add a container, clobbering anything on that path

    c = root.add_container(path="testbed", force=True)

    # Add a container with a slug (which Fedora may not honour)
    # The second of these will get a system-provided path

    s1 = c.add_container(metadata=my_rdf, slug="my_path")
    s2 = c.add_container(metadata=my_rdf, slug="my_path")
    
    # create some RDF and add a container with that metadata

    from rdflib import Graph, URIRef, Literal
    from rdflib.namespace import DC

    md = Graph()
    md.add(URIRef(''), DC.title, Literal('Document'))
    md.add(URIRef(''), DC.description, Literal('This is my document'))

    d = c.add_container(metadata=md, slug='Document')

    # dc_rdf is a shortcut for adding DC metadata

    md = repo.dc_rdf({ 'title': 'Document', 'description': 'This is simpler'})
    d2 = c.add_container(metadata=md, slug='Document2')

    # add a binary from a file
    # the 'basename' flag will use 'mypicture.jpg' as the slug
    
    d.add_binary(source='/export/data/my_picture.jpg', basename=True)

    # add a binary from a filehandle: in this case, you need to pass
    # in the mime type and slug

    with open('/export/data/my_picture.jpg', 'rb') as fh:
        d.add_binary(source=fh, mime='image/jpg', slug='my_picture.jpg')

    # add a binary from a URL - this uses the request library's
    # streaming API, so it won't pull the whole thing into memory
    # it gets the mime type from the HTTP request headers.

    d.add_binary(source='http://imgur.com/my_picture.jpg')

    # get a container

    c = repo.get(repo.path2uri('/testbed'))

    # access the rdf graph using rdflib

    for s, p, o in c.rdf:
        print("{} -> {}".format(str(p), str(o))

    # shortcut methods for looking up RDF predicates

    titles = c.rdf_get_all(DC.title)

## Docs

There's fairly comprehensive API documentation:

    pydoc -b fcrepo4


## Sample code

See this [sample script to upload spreadsheet data to Fedora 4](https://github.com/ptsefton/spreadsheet-to-fedora-commons-4).

## Tests

Note that test_016_access.py assumes a couple of test users on the Fedora
server.

A tomcat-users.xml with the correct users is in the tests/ directory. To
install it, copy it to /var/lib/tomcat7/conf/ on the fcrepo machine and 
restart Tomcat (sudo service tomcat7 restart)
