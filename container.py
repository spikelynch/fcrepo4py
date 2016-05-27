#!/usr/bin/env python

import requests, json, re, sys, logging

import fc4

fcurl = 'http://localhost:8080/fcrepo'
user = 'fedoraAdmin'
password = 'secret3'

repo = fc4.Repository(fcurl, user, password, loglevel=logging.DEBUG)

lg = logging.getLogger(__name__)
lg.setLevel(logging.DEBUG)

path = "test_path/assert_path"

metadata = {
    'title': 'New container',
    'description': 'Description of container',
    'creator': 'Mike Lynch'
    }

# print("ensure_container")
    
# response = repo.ensure_container(path, metadata)

# lg.info(response.status_code)

# response = repo.get(path)

# lg.info(response.status_code)

# try to create the same thing twice with PUT and then with POST

putpath = "test_path/put"

rdf = repo.dc_rdf("Put 1", "Description", "Creator")
headers = {'Content-Type': 'text/turtle'}

response = repo.api(putpath, method="PUT", headers=headers, data=rdf)
lg.info("Status = {}".format(response.status_code))
lg.info("Return = {}".format(response.text))

rdf = repo.dc_rdf("Put 2", "Description", "Creator")

response = repo.api(putpath, method="PUT", headers=headers, data=rdf)
lg.info("Status = {}".format(response.status_code))
lg.info("Return = {}".format(response.text))

postpath = "test_path/post"

rdf = repo.dc_rdf("Post 1", "Description", "Creator")
headers = {'Content-Type': 'text/turtle'}

response = repo.api(postpath, method="POST", headers=headers, data=rdf)
lg.info("Status = {}".format(response.status_code))
lg.info("Return = {}".format(response.text))

rdf = repo.dc_rdf("Post 2", "Description", "Creator")

response = repo.api(postpath, method="POST", headers=headers, data=rdf)
lg.info("Status = {}".format(response.status_code))
lg.info("Return = {}".format(response.text))

