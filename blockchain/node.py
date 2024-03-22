from loadbalanced_async_sharded_blockchain.common.config import Config
from loadbalanced_async_sharded_blockchain.blockchain.core import *
import logging
import traceback


logger = logging.getLogger(__name__)

class Node(object):

    def __init__(self, shard_no,no,B=10):
        self.shard_no = shard_no
        self.blockchain = BlockChain(shard_no)
        self.user_tree = UserTree()
        # self.no = str(uuid.uuid1()) 
        self.no = no
        self.B = B
        
        self.cache = []
        self.proposed = []
        self.commited = []
        self.local_block = None
        
        self.user_tree.add_user("0x11",100)
        self.user_tree.add_user("0x12",100)
        geneis_tx = Transaction.new(["0x11"],["0x12"],[shard_no],[shard_no],[10],"geneis tx payload")
        geneis_block = Block.new(0,"",[geneis_tx],[shard_no])
        self.blockchain.append(geneis_block)
        self.user_tree.update_user("0x11",90)
        self.user_tree.update_user("0x12",110)
        
        config = Config(self.no)
        self.concensus = HoneyBadgerBFTConcensus(config)

        self.load = 0
        
        
    def add_user(self,user_hash, balance):
        self.user_tree.add_user(user_hash, balance)
    
    def add_tx(self,transaction):
        from_shard_array = transaction.get('from_shard')
        to_shard_array = transaction.get('to_shard')
        if self.shard_no not in from_shard_array or self.shard_no not in to_shard_array:
            return
        self.cache.append(transaction)
        
    def select_transactions(self):
        self.commited = []
        self.proposed = self.cache[:self.B] 

    def new_block(self):
        if self.local_block:
            self.local_block = None
            
        index = self.blockchain.get_index()
        pre_hash = self.blockchain.last_block().get("hash")
        transactions = self.commited
        
        shard_array = set()
        for tx in transactions:
            from_shard_array = tx.get("from_shard")
            for shard in from_shard_array:
                shard_array.add(shard) 
            to_shard_array = tx.get("to_shard")
            for shard in to_shard_array:
                shard_array.add(shard)
            
        self.local_block = Block.new(index,pre_hash,transactions,list(shard_array))
        
    def add_block(self,):
        self.blockchain.append(self.local_block)
        
        # 更新用户数据
        saved_transactions = self.local_block.get("transactions")
        for tx in saved_transactions:
            from_hash = tx["from_hash"]
            to_hash = tx["to_hash"]
            old_from_amount = self.user_tree.get_balance(from_hash)
            old_to_amount = self.user_tree.get_balance(to_hash)
            self.user_tree.update_user(from_hash, old_from_amount - tx["amount"])
            self.user_tree.update_user(to_hash, old_to_amount + tx["amount"])
        
        # 清理旧交易
        saved_transactions_hash = [tx.get("hash") for tx in saved_transactions] 
        new_cache = []
        for tx in self.cache:
            if tx.get("hash") in saved_transactions_hash:
                continue
            new_cache.append(tx)
        self.cache = new_cache
        self.local_block = None
    
    def mine(self):
        while True:
            self.mine_onetime()
            if not self.cache:
                break

    def mine_onetime(self):
        self.select_transactions()
        a = time.time()
        try:
            logger.info('node:{} proposed {} transactions.'.format(self.no,len(self.proposed)))
            self.commited = self.concensus.concensus(self.proposed)
        except Exception as e:
            traceback.print_exc()
            logger.error(e)
            return
        self.new_block()
        self.add_block()
        b = time.time()
        logger.info("{}:mined one block. cost:{} s".format(self.no,b-a))
        self.load = self.concensus.get_load()
