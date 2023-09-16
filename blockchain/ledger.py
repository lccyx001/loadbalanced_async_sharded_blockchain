from loadbalanced_async_sharded_blockchain.blockchain.block import Block
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class Ledger(object):

    def __init__(self) -> None:
        self._shared_ledger = []

    def append(self,block:Block):
        """"""
        self._shared_ledger.append(block)
        logger.debug("append block:{}".format(block))

    def last_block(self):
        if not self._shared_ledger:
            return None
        return self._shared_ledger[-1]
    
    @property
    def ledger(self):
        return self._shared_ledger