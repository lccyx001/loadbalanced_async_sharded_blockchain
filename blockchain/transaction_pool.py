import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class TransactionPool(object):

    def __init__(self) -> None:
        self.local_tx_pool = []
    
    def append(self,tx):
        """
        :param tx: {'index': str,
                'from_hash': str,
                'to_hash': str,
                'amount': int}
        """
        # TODO check tx valid
        self.local_tx_pool.append(tx)

    def extend(self,txs):
        self.local_tx_pool.extend(txs)

    def clear_tx(self,block):
        """
        :param block: 
                {'index': str,
                 'nonce': int,
                 'previous_hash': str,
                 'timestamp': str,
                 'transactions': list[tx]}
        """
        confirmed_txs = [tx['index'] for tx in block['transactions']]
        self.local_tx_pool = [tx for tx in self.local_tx_pool if tx['index'] not in confirmed_txs]
        logger.info('shared txs cleared')

    def get_batch(self,batch=20):
        return self.local_tx_pool[:batch]
    
    def empty(self):
        return len(self.local_tx_pool) == 0

    def length(self):
        return len(self.local_tx_pool)