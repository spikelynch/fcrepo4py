"""An object representing a Fedora 4 transaction"""

from fcrepo4.exception import TransactionError
import requests


class Transaction(object):

    def __init__(self, repo):
        """Creates a new transaction object.

        TODO: this should be able to return to an existing transaction

        """

        self.repo = repo
        self.uri = None


    def __enter__(self):
        tx = self.repo.path2uri('/fcr:tx')
        response = self.repo.api(tx, method='POST')
        if response.status_code == requests.codes.created:
            self.uri = response.headers['Location']
            self.repo.logger.debug("Started transaction at {}".format(self.uri))
            return self
        else:
            message = "start transaction failed"
            raise TransactionError('/fcr:tx', self.user, response, message)



    def __exit__(self, ext, exv, traceback):
        self.repo.logger.debug("Transaction __exit__({}, {}, {})".format(ext, exv, traceback))
        if exv:
            self.repo.logger.warning("Rolling back after exception")
            self.rollback()
            self.repo.trx = None
            return False
        else:
            self.commit()
            self.repo.trx = None
            return True
        

    def path2uri(self, path):
        """Transform an api path so it's run in this transaction.

        This gets called from repository.api, which is the method all api
        calls go through.

        It detects calls to the transaction api and doesn't transform them.
        """

        if 'fcr:tx' in path:
            return self.repo.path2uri(path)
        return self.uri + '/' + path
        
    def keep_alive(self):
        """Ping the transaction so that it doesn't timeout"""
        return self.tx_api()

    def commit(self):
        """Commit the transaction"""
        return self.tx_api('commit')
        
    def rollback(self):
        """Abandon the transaction and rollback"""
        return self.tx_api('rollback')
        

    def tx_api(self, op=None):
        """Runs an operation against the tx api.

        Parameters

        op (str) - one of 'commit', 'keep_alive' or 'rollback'

        Returns true on success, raises a TransactionError otherwise
        
        """
        uri = self.uri + '/fcr:tx'
        if not op or op != 'keep_alive':
            uri += '/fcr:' + op
        # remember that the api will put tx keys in URLs
        response = self.repo.api(uri, method='POST')
        if response.status_code == requests.codes.no_content:
            return True
        raise TransactionError(uri, self.repo.user, response, op +" failed")

    
