from loadbalanced_async_sharded_blockchain.blockchain.blockchain import Blockchain
from loadbalanced_async_sharded_blockchain.blockchain.message import Message
import logging
from loadbalanced_async_sharded_blockchain.common.rpcbase import RPCBase
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils

logging.basicConfig(filename="log.log", level=logging.INFO)
logger = logging.getLogger(__name__)

class Server(RPCBase):

    def __init__(self,config,blockchain:Blockchain):
        broadcast_channels = config.channels
        host = config.host
        port = config.port
        self.id = config.id
        super(Server, self).__init__(broadcast_channels, host, port)
        self._blockchain = blockchain

    def broadcast(self, message):
        if not Message.validate(message):
            return
        
        for target_id,(adress,client) in self.remote_channels.items():
            logger.info("{} broadcast to:{}".format(self.id,target_id))
            client.receive(self.id,message)

    def receive(self, sender, message):
        # Print the received message
        logger.info("{} receive message from:{}".format(self.id,sender))
        msg_type, content, ts = message["msg_type"],message["content"],message["timestamp"]

        if msg_type == "transaction":
            self._receive_tx(content)

        if msg_type == "block":
            self._blockchain.receive_block(content)

    def _receive_tx(self,tx_json):
        tx = Utils.json_to_dict(tx_json)
        self._blockchain.receive_txs([tx])

    def _receive_block(self,block_json):
        block = Utils.json_to_dict(block_json)
        self._blockchain.receive_block(block)