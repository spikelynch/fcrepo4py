import unittest
import fcrepo4

class FCRepoTest(unittest.TestCase):

    def setUp(self):
        self.repo = fcrepo4.Repository()

