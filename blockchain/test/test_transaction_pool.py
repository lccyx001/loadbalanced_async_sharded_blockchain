from loadbalanced_async_sharded_blockchain.blockchain.transaction_pool import TransactionPool
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
from loadbalanced_async_sharded_blockchain.blockchain.block import Block
from loadbalanced_async_sharded_blockchain.blockchain.utils import Utils
import random

def test_transaction_pool():
    tx_pool = TransactionPool()
    assert tx_pool.empty()

    txs = [] 
    for i in range(20):
        tx_data = {"index":i,"from_hash":"test","to_hash":"test1","amount":random.random()}
        txs.append(Transaction.new(tx_data))
    tx_pool.extend(txs)

    tx_single = {"index":20,"from_hash":"test","to_hash":"test1","amount":random.random()}
    tx_pool.append(tx_single)
    
    assert not tx_pool.empty()

    tx_to_block = tx_pool.get_batch()
    
    block = Block.forge(0,Utils.compute_hash("hello"),tx_to_block)
    tx_pool.clear_tx(block)
    
    assert not tx_pool.empty()


if __name__ == "__main__":
    test_transaction_pool()