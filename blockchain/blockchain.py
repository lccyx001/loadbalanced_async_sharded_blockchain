import logging
from loadbalanced_async_sharded_blockchain.blockchain.block import Block
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
from loadbalanced_async_sharded_blockchain.blockchain.transaction_pool import TransactionPool
from loadbalanced_async_sharded_blockchain.blockchain.ledger import Ledger
import gevent
from gevent.event import Event
from loadbalanced_async_sharded_blockchain.honeybadgerbft.honeybadger import HoneyBadgerBFT
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class Lock(object):

    def __init__(self) -> None:
        self._lock = Event()
        self._lock.clear()

    def lock(self):
        self._lock.set()

    def in_use(self):
        return self._lock.ready()
    
    def unlock(self):
        self._lock.clear()

class Blockchain(object):
    
    def __init__(self, config):
        self._config = config
        self.tx_pool = TransactionPool()
        self._ledger = Ledger()
        
        self.local_tx = []
        self.count_tx = 0
        self.local_block = None
        self._local_block_lock = Lock()

        self.shared_ledger = []

        _port = config.honeybadger_port
        _channel = config.honeybadger_channels
        _host = config.honeybadger_host
        client = ClientBase(_channel,_host,_port,config.N,config.id)
        self._rpc_thread = gevent.spawn(client.run_forever)
        gevent.spawn(client.connect_broadcast_channel)
        self._client = client
        pid = self._config.id
        self._pid = pid
        self._sid = "SID"
        



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
        #TODO: cocurrent logic

        # if self._local_block_lock.in_use():
        #     return False
        
        # self._local_block_lock.lock()

        self._set_local_block(Block.forge(self.last_block['index'] + 1, self.last_block['hash'], transactions))
        logger.info("{} forge block.".format(self._pid))

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
        self._client.reset()
        
        #TODO:local block may be none
        hbbft = HoneyBadgerBFT(self._sid, self._pid,self._client)
        hbbft.submit_txs(Utils.dict_to_json(self.local_block["transactions"]))
        gl = gevent.spawn(hbbft.run)
        comfirmed_txjson = gl.get()
        assert comfirmed_txjson is not None
        
        comfirmed_txs = []
        for txjson in comfirmed_txjson:
            txs = Utils.json_to_dict(txjson)
            comfirmed_txs.extend(txs)
        self.local_block["transactions"] = comfirmed_txs
        
        block = self.local_block
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

    # def _get_local_block(self):
    #     return self.local_block
    
    def _set_local_block(self,block):
        # if self._local_block_lock.in_use():
        #     return False
        self.local_block = block

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