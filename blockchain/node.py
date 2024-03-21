from loadbalanced_async_sharded_blockchain.common.config import Config
from loadbalanced_async_sharded_blockchain.blockchain.core import *
import logging
import traceback
import copy

logger = logging.getLogger(__name__)

class Node(object):

    def __init__(self, shard_no):
        self.shard_no = shard_no
        self.blockchain = BlockChain(shard_no)
        self.user_tree = UserTree()
        self.no = str(uuid.uuid1()) 
        
        self.cache = []
        self.local_block = None
        
        self.user_tree.add_user("0x11",100)
        self.user_tree.add_user("0x12",100)
        geneis_tx = Transaction.new("0x11","0x12",shard_no,shard_no,10,"geneis tx payload")
        geneis_block = Block.new(0,"",[geneis_tx],[shard_no])
        self.blockchain.append(geneis_block)
        self.user_tree.update_user("0x11",90)
        self.user_tree.update_user("0x12",110)
    
    
    def add_tx(self,transaction):
        self.cache.append(transaction)
    
    def new_block(self):
        if self.local_block:
            self.local_block = None
            
        index = self.blockchain.get_index()
        pre_hash = self.blockchain.last_block().get("hash")
        transactions = copy.deepcopy(self.cache) 
        shard_array = set()
        for tx in transactions:
            shard_array.add(tx.get("from_shard"))
            shard_array.add(tx.get("to_shard"))
            
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
            self.new_block()
            try:
                self.block_chain.honeybadgerbft()
            except Exception as e:
                traceback.print_exc()
                logger.error(e)
                continue
            self.add_block()
            logger.info("{}:mined one block.".format(self.no))

    def mine_onetime(self):
        # if not self.block_chain.ready():
        #     return
            # logger.info("not ready,now sleep")
            # time.sleep(3)
            # break  # for test
            # continue
        
        self.block_chain.forge_block()
        try:
            self.block_chain.honeybadgerbft()
        except Exception as e:
            traceback.print_exc()
            logger.error(e)
        self.block_chain.add_block()
        logger.info("{}:mined one block.".format(self.id))

    def mock_account(self,accounts):
        for acc in accounts:
            self.block_chain.account.mock_account(acc)
