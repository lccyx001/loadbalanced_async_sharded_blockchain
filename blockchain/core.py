import uuid
from hashlib import sha256
import json
import logging
import time
import gevent
from loadbalanced_async_sharded_blockchain.honeybadgerbft.honeybadger import HoneyBadgerBFT
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase


def compute_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return sha256(json_data.encode()).hexdigest()

class Transaction(object):
    
    @staticmethod
    def new(from_hash_array,to_hash_array,from_shard_array,to_shard_array,amount_array,payload):
        raw_data = {
            "index":str(uuid.uuid1()),
            "from_hash":from_hash_array,
            "to_hash":to_hash_array,
            "from_shard":from_shard_array,
            "to_shard":to_shard_array,
            "amount":amount_array,
            "payload":payload,
            }
        tx_hash = compute_hash(raw_data)
        raw_data.update({"hash":tx_hash})
        return raw_data

class UserTree(object):

    def __init__(self) -> None:
        self.tree = {}
        
    def add_user(self,user_hash,balance):
        if user_hash in self.tree:
            return
        self.tree[user_hash] = balance

    def update_user(self,user_hash,balance):
        self.tree[user_hash] = balance

    def get_balance(self,user_hash):
        return self.tree.get(user_hash,0)
    
class Block(object):

    @staticmethod
    def new(index, pre_hash, transactions, shard_array):
        raw_block = {
            "index":index,
            "pre_hash":pre_hash,
            "transactions":transactions,
            "shard":shard_array
        }
        block_hash = compute_hash(raw_block)
        timestamp = int(time.time() * 1000)
        raw_block.update({
            "hash":block_hash,
            "timestamp":timestamp
        })
        return raw_block
    
    
class BlockChain(object):

    def __init__(self,shard_no) -> None:
        self.shard = shard_no
        self.ledger = []

    def append(self,block):
        self.ledger.append(block)

    def get_ledger(self):
        return self.ledger
    
    def get_index(self):
        return len(self.ledger)+1
    
    def last_block(self):
        return self.ledger[-1]
    
class HoneyBadgerBFTConcensus(object):
    
    logger = logging.getLogger("HoneyBadgerBFTConcensus")
    
    def __init__(self,config,) -> None:
        
        client = ClientBase(config.honeybadger_channels,config.honeybadger_host,config.honeybadger_port,config.N,config.id)
        
        self.rpc_thread = gevent.spawn(client.run_forever)
        gevent.spawn(client.connect_broadcast_channel)
        self.client = client
        self.sid = "HoneyBadgerSID"
        self.pid = config.id
        
    def concensus(self, transactions):
        self.client.reset()
        
        hbbft = HoneyBadgerBFT(self.sid, self.pid,self.client)
        hbbft.submit_txs(json.dumps(transactions,sort_keys=True))
        gl = gevent.spawn(hbbft.run)
        comfirmed_txjson = gl.get()
        
        if not comfirmed_txjson :
            self.logger.info("failed one round concensus")
            return []
        
        comfirmed_txs = []
        for txjson in comfirmed_txjson:
            txs = json.loads(txjson)
            comfirmed_txs.extend(txs)
        self.logger.info("finish one round concensus, txs:{}".format(len(comfirmed_txs)))
        
        return comfirmed_txs
    
    def get_load(self,):
        return self.client.load