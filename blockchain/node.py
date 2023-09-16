import time
from blockchain import Blockchain
from server import Server
from message import Message
from common.config import Config
import logging
import gevent

class Node(object):

    def __init__(self, id):
        self.id = id
        
        config = Config(id)
        block_chain =Blockchain(config)
        server = Server(id,config.host,config.port,config.channels,block_chain)

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
        return len(self.block_chain.ledger)
    

    def forge_genesis_block(self):
        return self.block_chain.forge_genesis_block()
    
    def mine(self):
        while True:

            if self.block_chain.ready():
                time.sleep(3)
                continue

            self.block_chain.forge_block()
            self.block_chain.honeybadgerbft()
            self.block_chain.add_block()
            message = Message.create("block",self.block_chain.last_block)
            self.server.broadcast(message)
            