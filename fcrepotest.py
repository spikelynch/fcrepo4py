import unittest, logging
import fcrepo4

class FCRepoTest(unittest.TestCase):

    def setUp(self, loglevel=logging.WARNING):
        self.repo = fcrepo4.Repository(loglevel=loglevel)

