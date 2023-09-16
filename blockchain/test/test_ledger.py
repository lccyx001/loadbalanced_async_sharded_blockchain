from loadbalanced_async_sharded_blockchain.blockchain.block import Block
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
from loadbalanced_async_sharded_blockchain.blockchain.ledger import Ledger
import random

def make_block():
    txs = [] 
    for i in range(10):
        tx_data = {"index":i,"from_hash":"test","to_hash":"test1","amount":random.random()}
        txs.append(Transaction.new(tx_data))

    p_hash = Utils.compute_hash("hello")
    block = Block.forge(0,p_hash,txs)
    return block

def test_ledger():
    block = make_block()
    ledger = Ledger()
    ledger.append(block)
    assert ledger.last_block() == block
    assert len(ledger.ledger) == 1
    


if __name__ == "__main__":
    test_ledger()