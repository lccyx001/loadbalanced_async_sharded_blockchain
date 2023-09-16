import logging
from loadbalanced_async_sharded_blockchain.blockchain.block import Block
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
from loadbalanced_async_sharded_blockchain.blockchain.transaction_pool import TransactionPool
from loadbalanced_async_sharded_blockchain.blockchain.ledger import Ledger
import gevent
from loadbalanced_async_sharded_blockchain.honeybadgerbft.honeybadger import HoneyBadgerBFT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class Blockchain(object):
    
    def __init__(self, config):
        # self.server = None # used for communcation
        self._config = config
        self.tx_pool = TransactionPool()
        self._ledger = Ledger()
        
        self.local_tx = []
        self.count_tx = 0
        self.local_block = None
        
        self.shared_ledger = []

    @property
    def last_block(self):
        return self._ledger.last_block()
    
    @property
    def ledger(self):
        return self._ledger.ledger

    def ready(self):
        return not self.tx_pool.empty()

    def forge_genesis_block(self):
        # TODO:only call one time
        genesis_hash = "genesis block hash"
        genesis_block = Block.forge(0, genesis_hash, [])
        genesis_block['hash'] = Utils.compute_hash(genesis_block)
        self._ledger.append(genesis_block)
        logging.info('Genesis block was created.')

    def forge_block(self):
        transactions = self.tx_pool.get_batch()
        self.local_block = Block.forge(self.last_block['index'] + 1, self.last_block['hash'], transactions)

    def submit_tx(self, data):
        """
        :param data: {'from_hash': str,'to_hash': str,'amount': int}
        """
        data['index'] = self._get_tx_num()
        tx_raw = Transaction.new(data)
        try:
            self.tx_pool.append(tx_raw)
        except Exception as e:
            self.count_tx -= 1
            logger.error(e)

    def receive_txs(self,txs):
        self.tx_pool.extend(txs)

    def honeybadgerbft(self,):
        sid = "SID"
        pid = self._config.id
        hbbft = HoneyBadgerBFT(sid, pid, Utils.dict_to_json(self.local_block["transactions"]))
        gl = gevent.spawn(hbbft.run)
        
        comfirmed_txjson = gl.get()
        comfirmed_txs = []
        for txjson in comfirmed_txjson:
            txs = Utils.json_to_dict(txjson)
            comfirmed_txs.extend(txs)
        self.local_block["transactions"] = comfirmed_txs
        
        block = self.local_block
        logger.info("get hbbft block {}".format(block))
        computed_hash = Utils.compute_hash(block)
        self.local_block['hash'] = computed_hash
        logger.info("finish one round concensus")
    
    def add_block(self):
        self._add_block()

    def receive_block(self,block):
        if not Block.validate(block):
            return False
        
        if not self._validate_previous_hash(block):
            return False
        
        self.local_block = block
        self._add_block()

    def _add_block(self):
        block = self.local_block
        self.ledger.append(block)
        self.tx_pool.clear_tx(block)
        self._clear_local_block()
        logger.info('Block #{} was inserted into the ledger'.format(block['index']))

    def _get_tx_num(self):
        self.count_tx += 1
        return self.count_tx

    def _clear_local_block(self):
        self.local_block = None

    def _validate_previous_hash(self, block_raw):
        last_block = self.last_block
        if not last_block:
            return False
        if block_raw['previous_hash'] != last_block['hash']:
            logging.error('Blockchain: Block: #{} previous_hash is not valid!'.format(block_raw['index']))
            return False
        return True