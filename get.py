#!/usr/bin/env python3

import fc4, requests

fcurl = 'http://localhost:8080/fcrepo'
user = 'fedoraAdmin'
password = 'secret3'

repo = fc4.Repository(fcurl, user, password)

response = repo.get('/fcr:accessroles', format='application/ld+json')

print(response.text)
