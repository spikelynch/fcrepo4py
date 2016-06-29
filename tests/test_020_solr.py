import unittest
import fcrepo4, fcrepotest
import logging, requests, json, time
from rdflib import Literal, URIRef
from rdflib.namespace import DC, Namespace
import random

CPATH = 'test_020'

ENTRIES = 'tests/glossatory.txt'
#ENTRIES = 'tests/short.txt'
LOGMOD = 10
MAXIMUM = 30

SOLR_PAUSE = 60

CREATORS = [ 'Alice', 'Bob', 'Carol', 'Dave', 'Ernie', 'Fred', 'Georgina' ]

CMDATA = {
    'title': 'Container',
    'description': 'Container for lots of solr entries',
    'creator': 'a test script'
    }


class TestSolr(fcrepotest.FCRepoContainerTest):
    
    def setUp(self):
        super(TestSolr, self).setUp(CPATH, CMDATA, loglevel=logging.INFO)

    def tearDown(self):
        super(TestSolr, self).tearDown(CPATH)
            
    def test_solr(self):
        """Takes a file of plausible gibberish and makes lots of resources"""
        c = self.repo.get(self.repo.path2uri(CPATH))
        global MAXIMUM

        entries = {}
        with open(ENTRIES, 'r') as fh:
            for line in fh:
                l = line.split(': ')
                if len(l) == 2:
                    if len(l[0]) > 0:
                        entries[l[0]] = l[1]

        if not MAXIMUM:
            MAXIMUM = len(entries)
        self.logger.info("Adding {} resources".format(MAXIMUM))
        n = 0
        resources = {}
        for title, description in entries.items():
            creator = random.choice(CREATORS)
            md = self.repo.dc_rdf({
                'title': title,
                'description': description,
                'creator': creator
                })
            c.add_container(md)
            resources[title] = description
            n += 1
            if n % LOGMOD == 0:
                self.logger.info("{}: {}".format(n, title))
            if n > MAXIMUM:
                self.logger.info("Maximum reached: {}".format(MAXIMUM))
                break

        self.logger.info("Sleeping for {}s to let solr catch up".format(SOLR_PAUSE))
        time.sleep(SOLR_PAUSE)

        self.logger.info("Trying solr lookup for all resources")
        for title, description in resources.items():
            json = self.solr_lookup({ 'title': title }) 
            self.assertIsNotNone(json)
            n = None
            if 'response' in json:
                if 'numFound' in json['response']:
                    n = json['response']['numFound']
            self.assertIsNotNone(n)
            self.assertTrue(n > 0)
            

    def solr_lookup(self, query):
        """Very basic, ANDS all query parameters"""
        solr = self.repo.cf['solr_uri']
        q = [ f + ':' + v for f, v in query.items() ]
        params = {}
        params['q'] = ' AND '.join(q)
        params['wt'] = 'json'
        r = requests.get(solr, params=params)
        if r.status_code == requests.codes.ok:
            return json.loads(r.text)
        else:
            self.logger.error("Solr error: {} {}".format(r.status_code, r.reason))
            return None
        
        
if __name__ == '__main__':
    unittest.main()
