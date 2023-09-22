from loadbalanced_async_sharded_blockchain.blockchain.server import Server
from loadbalanced_async_sharded_blockchain.common.config import Config
from loadbalanced_async_sharded_blockchain.blockchain.blockchain import Blockchain
from loadbalanced_async_sharded_blockchain.blockchain.message import Message
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
from loadbalanced_async_sharded_blockchain.blockchain.block import Block
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils
import gevent
import random

def _init_server():
    servers = []
    bcs = []
    for i in range(4):
        config = Config(i)
        bc = Blockchain(config)
        server = Server(config,bc)
        gevent.spawn(server.run_forever)
        gevent.spawn(server.connect_broadcast_channel)
        server._blockchain.forge_genesis_block()
        servers.append(server)
        bcs.append(bc)
    return servers,bcs

def test_broadcast_transaction():
    servers,bcs = _init_server()
    
    bc = bcs[0]
    server = servers[0]

    tx = Transaction.new({"from_hash":"test","to_hash":"test","amount":1,"index":0})
    bc.submit_tx(tx)
    m = Message.create("transaction",tx)
    gl = gevent.spawn(server.broadcast,m) 
    gl.get()
    for i in range(4):
        assert bcs[i].ready()

def test_broadcast_block():
    servers,bcs = _init_server()
    bc = bcs[0]
    server = servers[0]
    
    for i in range(10):
        tx_data = {"index":i+10,"from_hash":"test","to_hash":"test1","amount":random.randint(1,100)}
        bc.submit_tx(tx_data)
    bc.forge_block()
    m = Message.create("block",bc.local_block)
    gl = gevent.spawn(server.broadcast,m) 
    gl.get()
    bc.add_block()
    for i in range(4):
        print(i)
        assert len(bcs[i].ledger) == 2

if __name__ =="__main__":
    # test_broadcast_transaction()
    test_broadcast_block()
