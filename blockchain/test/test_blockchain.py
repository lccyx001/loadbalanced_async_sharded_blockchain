from loadbalanced_async_sharded_blockchain.blockchain.blockchain import Blockchain
from loadbalanced_async_sharded_blockchain.common.config import Config
from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction
import random
import gevent

def test_blockchain():
    cfg = Config(0)
    bc = Blockchain(cfg)
    
    # test last block, ledger, ready
    assert not bc.last_block
    assert not bc.ledger
    assert not bc.ready()
    
    # test forge_genesis_block
    bc.forge_genesis_block()
    genesis_block = bc.last_block

    assert bc.last_block
    assert len(bc.ledger)  == 1
    assert not bc.ready()
    
    # test submit tx
    for i in range(10):
        tx_data = {"from_hash":"test","to_hash":"test1","amount":random.random()}
        bc.submit_tx(tx_data)
    assert bc.ready()
    

    # test receive_txs
    txs = []
    for i in range(10):
        tx_data = {"index":i+10,"from_hash":"test","to_hash":"test1","amount":random.random()}
        txs.append(Transaction.new(tx_data))
    bc.receive_txs(txs)
    assert len(bc.tx_pool.local_tx_pool) == 20
    

def test_blockchain_honeybadger():
    gls = []
    bcs = []
    txs = []
    for _ in range(4):
        txs.append([])

    for j in range(20):
        tx_data = {"from_hash":"test{}".format(j),"to_hash":"test{}".format(j),"amount":random.random()}
        txs[j%4].append(tx_data)

    for i in range(4):
        cfg = Config(i)
        bc = Blockchain(cfg)
        bc.forge_genesis_block()
        for _,tx in enumerate(txs[i]):
            bc.submit_tx(tx)

        bc.forge_block()
        gl = gevent.spawn(bc.honeybadgerbft)
        gls.append(gl)
        bcs.append(bc)
    gevent.joinall(gls)
    blocks = [_.local_block for _ in bcs]
    block_hash = blocks[0]["hash"]
    for b in blocks:
        assert block_hash == b["hash"]
        assert len(b["transactions"]) == 20
    
    bcs[0].add_block()
    bcs[1].receive_block(bcs[0].last_block)
    assert bcs[0].last_block["hash"] == block_hash
    assert bcs[1].last_block["hash"] == block_hash
    assert len(bcs[0].ledger) == 2
    assert not bcs[1].ready()

if __name__ == "__main__":
    # test_blockchain()
    test_blockchain_honeybadger()