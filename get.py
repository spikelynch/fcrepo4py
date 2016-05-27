#!/usr/bin/env python3

import fcrepo4, requests, logging

#fcurl = 'http://localhost:8080/fcrepo'
#user = 'fedoraAdmin'
#password = 'secret3'

print("Connecting")

repo = fcrepo4.Repository(loglevel=logging.DEBUG)

print(repo)

response = repo.get('/')

print(response.text)
