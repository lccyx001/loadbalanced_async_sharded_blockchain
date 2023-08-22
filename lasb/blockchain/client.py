import zerorpc
from blockchain import Blockchain
from message import Message
import logging

class Client(object):

    def __init__(self, name):
        self.name = name
        self.peers = []
        self.shared_ledger = []
        self.shared_tx = []
        self.block_chain =Blockchain(self)

    def connect(self, address):
        # Connect to a peer node at the specified address
        client = zerorpc.Client()
        client.connect(address)
        self.peers.append(client)
        logging.info("connected to",address)

    def is_any_node_alive(self):
        return True

    def broadcast(self, message):
        # Send a message to all connected peers
        for peer in self.peers:
            print(self.name,"send message",message)
            peer.receive(self.name, message)
    
    # P2P Client Tractions API
    def new_tx(self,data):
        return self.block_chain.new_tx(data)
    
    # P2P Client Blocks API
    def get_server_ledger(self):
        if self.shared_ledger:
            return self.shared_ledger
        return False

    def get_ledger_size(self):
        return len(self.shared_ledger)

    def request_add_block(self):
        return self.block_chain.request_add_block()

    def forge_genesis_block(self):
        return self.block_chain.forge_genesis_block()
    
    def forge_block(self):
        return self.block_chain.forge_block()
    
    def honeybadgerbft(self):
        return self.block_chain.honeybadgerbft()
    
    def network(self,addresses):
        return self.broadcast(Message().create(msg_type="network",flag=1,content=addresses))
    