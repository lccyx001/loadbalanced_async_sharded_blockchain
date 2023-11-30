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

def _generate_account():
    accounts = []
    for _ in range(20):
        accounts.append("test{}".format(_))


    return accounts

def _generate_txs():
    txs = []
    accounts = _generate_account()
    for _ in range(4):
        txs.append([])

    for j in range(400):
        tx_data = {"from_hash":accounts[random.randint(0,19)],"to_hash":accounts[random.randint(0,19)],"amount":random.randint(1,100)}
        txs[j%4].append(tx_data)
    return txs,accounts

def test_mine():
    nodes = _init_nodes()
    txs,accs = _generate_txs()
    gls = []
    for idx,node in enumerate(nodes):
        assert node.get_ledger()
        assert node.get_ledger_size() == 1
        node.mock_account(accs)
        for tx in txs[idx]:
            node.submit_tx(tx)    
        gl = gevent.spawn(node.mine_onetime) 
        gls.append(gl)
    
    gevent.joinall(gls)
    
    for node in nodes:
        print(node.get_ledger_size())
        print(node.block_chain.account._accounts_db)
        # assert node.get_ledger_size() == 2

if __name__ =="__main__":
    test_mine()
