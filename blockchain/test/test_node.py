from loadbalanced_async_sharded_blockchain.blockchain.node import Node
import gevent
import random

def _init_nodes():
    nodes = []
    for i in range(4):
        node = Node(i)
        node.forge_genesis_block()
        nodes.append(node)        
    return nodes

def _generate_txs():
    txs = []
    for _ in range(4):
        txs.append([])

    for j in range(400):
        tx_data = {"from_hash":"test{}".format(j),"to_hash":"test{}".format(j),"amount":random.random()}
        txs[j%4].append(tx_data)
    return txs

def test_mine():
    nodes = _init_nodes()
    txs = _generate_txs()
    gls = []
    for idx,node in enumerate(nodes):
        assert node.get_ledger()
        assert node.get_ledger_size() == 1
        for tx in txs[idx]:
            node.submit_tx(tx)    
        gl = gevent.spawn(node.mine) 
        gls.append(gl)
    
    gevent.joinall(gls)
    
    for node in nodes:
        print(node.get_ledger_size())
        # assert node.get_ledger_size() == 2

if __name__ =="__main__":
    test_mine()
