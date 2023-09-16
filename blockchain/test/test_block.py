from loadbalanced_async_sharded_blockchain.blockchain.block import Block
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
import random

def test_block():
    txs = [] 
    for i in range(10):
        tx_data = {"index":i,"from_hash":"test","to_hash":"test1","amount":random.random()}
        txs.append(Transaction.new(tx_data))

    p_hash = Utils.compute_hash("hello")
    block = Block.forge(0,p_hash,txs)
    print(block)

if __name__ == "__main__":
    test_block()