import zerorpc
from blockchain import Blockchain
from message import Message
import logging
import time
logging.basicConfig(filename="test.log", level=logging.INFO)
logger = logging.getLogger("server")

class Server(object):

    def __init__(self, name,host,port):
        self.name = name
        self.host = host
        self.port = port
        self.address = "tcp://{}:{}".format(self.host,self.port)
        self.peers = []
        self.connected_address = []
        self.shared_ledger = []
        self.shared_tx = []
        self.block_chain =Blockchain(self)

    def p2p_connect(self, addresses):
        # Connect to all peers node at the specified address
        for address in addresses:
            print(address==self.address)
            if address == self.address:
                continue
            if address in self.connected_address:
                continue
            s2s_client =zerorpc.Client()
            s2s_client.connect(address)
            self.peers.append(s2s_client)
            logger.info("connect to :{}".format(address))

    # P2P Server API
    def broadcast(self, message):
        # Send a message to all connected peers
        for peer in self.peers:
            logger.info(self.name,"send message",message)
            peer.receive(self.name, message)


    def receive(self, sender, message):
        # Print the received message
        print(self.name,"receive from:",sender,"data:",message)
        logger.info(self.name,"receive from:",sender,"data:",message)
        if not Message.validate(message):
            logger.error("Invalid Messages",message)
            return (sender,message)
        if message['msg_type'] == "network" and message['flag']==1:
            self.p2p_connect(message["content"])

        if message['msg_type'] == "transaction" and message['flag']==1:
            self.block_chain.receive_txs(message['content'])

        if message['msg_type'] == "block" and message['flag']==1:
            self.block_chain.receive_block(message['content'])

        return (sender,message)
    
    def is_any_node_alive(self):
        return True
    

def run_forever(node):
    server = zerorpc.Server(node)
    address = "tcp://{}:{}".format(node.host,node.port)
    server.bind(address)
    logger.info("starting node server",node.name)
    server.run()
    
