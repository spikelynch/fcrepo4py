#!/usr/bin/env python

import fcrepo4

repo = fcrepo4.Repository()


repo.set_user('fedoraAdmin')

rdf = repo.dc_rdf({'title': "ACL Testbed"})

print(rdf)

root = repo.get(repo.path2uri('/'))

container = root.add_container(rdf, path="acl_testbed", force=True)

repo.set_user('user')


acls = container.acl_get()
print(acls)
