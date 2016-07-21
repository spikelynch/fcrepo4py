import unittest
import fcrepo4, fcrepotest
import logging, requests

from fcrepo4.exception import Error



CPATH = 'test_018'
    
CMDATA = {
    'title': 'Container',
    'description': 'A test container for transactions',
    'creator': 'test_018_transaction.py'
    }

    
SLUG = 'slug'

class TestTransaction(fcrepotest.FCRepoContainerTest):

    def setUp(self):
        super(TestTransaction, self).setUp(CPATH, CMDATA, loglevel=logging.INFO)

    def tearDown(self):
        super(TestTransaction, self).tearDown(CPATH)


    def test_complete_transaction(self):
        """Perform some operations inside a transaction that succeeds"""

        c = self.container

        kids = []

        with self.repo.transaction() as t:
            for i in range(1, 6):
                g = self.repo.dc_rdf({ 'title': 'kid {}'.format(i)})
                kids.append(c.add_container(g))

        self.assertIsNone(self.repo.trx)

        c = self.repo.get(self.repo.path2uri(CPATH))
        
        for kuri in c.children():
            k2 = self.repo.get(kuri)
            self.assertIsNotNone(k2)


    def test_complete_transaction(self):
        """Perform some operations inside a transaction that fails"""

        c = self.container

        kids = []

        try:
            with self.repo.transaction() as t:
                for i in range(1, 3):
                    g = self.repo.dc_rdf({ 'title': 'kid {}'.format(i)})
                    kids.append(c.add_container(g))
                raise(Error("This whole thing is over"))
                for i in range(4, 6):
                    g = self.repo.dc_rdf({ 'title': 'kid {}'.format(i)})
                    kids.append(c.add_container(g))
        except Error as e:
            pass
        
        self.assertIsNone(self.repo.trx)

        c = self.repo.get(self.repo.path2uri(CPATH))

        children = list(c.children())
        self.assertEqual(len(children), 0)
        

                                            
if __name__ == '__main__':
    unittest.main()
