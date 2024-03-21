import uuid
from hashlib import sha256
import json
import logging
import time

def compute_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return sha256(json_data.encode()).hexdigest()

class Transaction(object):
    
    @staticmethod
    def new(from_hash,to_hash,from_shard,to_shard,amount,payload):
        raw_data = {
            "index":str(uuid.uuid1()),
            "from_hash":from_hash,
            "to_hash":to_hash,
            "from_shard":from_shard,
            "to_shard":to_shard,
            "amount":amount,
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
    