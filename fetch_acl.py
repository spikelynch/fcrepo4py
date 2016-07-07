#!/usr/bin/env python

# proof-of-concept - python script to fetch the effective ACLs of any
# fedora container via the rel="acl" header

import fcrepo4, logging, argparse, re, json
from rdflib import Literal, URIRef

def acl_link(headers):
    link_re = re.compile('<([^>]*)>; *rel="acl"')
    if 'Link' in headers:
        m = link_re.search(headers["Link"])
        if m:
            return m.group(1)
    return None
            


def fetch_acls(repo, uri):
    repo.set_user('fedoraAdmin')
    resource = repo.get(uri)
    if not resource:
        print("Fedora object {} not found".format(uri))
        return None
    acl_uri = acl_link(resource.response.headers)
    if not acl_uri:
        print("uri has no effective acl")
        return None
    acl = repo.get(acl_uri)
    if not acl:
        print("acl at uri {} not found".format(acl_uri))
        return None
    return json.dumps(acl.acls())




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('uri', type=str, help="A Fedora URI")
    parser.add_argument('-c', '--config', default="config.yml", type=str, help="Config file")
    args = parser.parse_args()
    repo = fcrepo4.Repository(config=args.config)
    permissions = fetch_acls(repo, args.uri)
    print(permissions)
