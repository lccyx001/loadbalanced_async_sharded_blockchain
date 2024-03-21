from loadbalanced_async_sharded_blockchain.blockchain.core import *
from loadbalanced_async_sharded_blockchain.blockchain.node import Node

if __name__ == "__main__":
    print("----------------test Node----------------")
    node = Node(1)
    
    txdata = {"from_hash":"0x11","to_hash":"0x12","amount":10}
    tx = Transaction.new(txdata["from_hash"],txdata["to_hash"],1,2,100,"something payload")
    node.add_tx(tx)
    node.new_block()
    node.add_block()
    assert len(node.blockchain.ledger) == 2
    print("success")