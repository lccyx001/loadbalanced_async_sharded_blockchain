import time
from loadbalanced_async_sharded_blockchain.blockchain.blockchain import Blockchain
from loadbalanced_async_sharded_blockchain.blockchain.server import Server
from loadbalanced_async_sharded_blockchain.blockchain.message import Message
from loadbalanced_async_sharded_blockchain.common.config import Config
import logging
import gevent
import traceback

logger = logging.getLogger(__name__)

class Node(object):

    def __init__(self, id):
        self.id = id
        
        config = Config(id)
        block_chain =Blockchain(config)
        server = Server(config,block_chain)

        self.server_let = gevent.spawn(server.run_forever)
        server.connect_broadcast_channel()

        self.server = server
        self.block_chain = block_chain
    
    def submit_tx(self,data):
        """
        param data: 
        {   'from_hash': str,
            'to_hash': str,
            'amount': int 
            }
        """
        return self.block_chain.submit_tx(data)
    
    
    def get_ledger(self):
        return self.block_chain.ledger

    def get_ledger_size(self):
        return len(self.get_ledger())

    def forge_genesis_block(self):
        return self.block_chain.forge_genesis_block()
    
    def mine(self):
        while True:

            if not self.block_chain.ready():
                return
                logger.info("not ready,now sleep")
                time.sleep(3)
                break  # for test
                continue
            
            self.block_chain.forge_block()
            try:
                self.block_chain.honeybadgerbft()
            except Exception as e:
                traceback.print_exc()
                logger.error(e)
                continue
            self.block_chain.add_block()
            logger.info("{}:mined one block.".format(self.id))

    def ping_pong(self):
        pass
