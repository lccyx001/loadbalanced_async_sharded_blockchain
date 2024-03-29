import sys
sys.path.append(r'../../..')

import yaml
from loadbalanced_async_sharded_blockchain.blockchain.core import *
from loadbalanced_async_sharded_blockchain.blockchain.node import Node
import random
from faker import Faker
fake = Faker()

def get_nodes(shard_no, no_start,no_end, B):
    nodes = [Node(shard_no, i, B) for i  in range(no_start,no_end+1)]
    return nodes

def generate_random_str(randomlength=16):
    """
    生成一个指定长度的随机字符串
    """
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str

def generateTransactions(number, cross_proportion=0):
    txs = []
    cross = 0
    for i in range(number):
        from_hash = compute_hash(i)
        to_hash = compute_hash(str(i)+"s")
        amount = random.randint(0, 300)
        if not cross_proportion:
            from_shard = [shard_no]
            to_shard = [shard_no]
        else:
            if(i/number <= cross_proportion):
                from_shard = [ random.randint(0,shard_number) ]
                to_shard = [ (from_shard[0] +1 ) % shard_number ]
                cross += 1
            else:
                from_shard = to_shard = [shard_no]
        payload = generate_random_str(stringlength)
        txs.append(Transaction.new(from_hash,to_hash,from_shard,to_shard,amount,payload))
    print("generate transactions:total:", number, "cross:", cross)
    return txs

def send_txs(nodes, transactions):
    for idx,tx in enumerate(transactions) :
        node_id = idx % node_pershard
        node = nodes[node_id]
        # print("send tx to",node.no,"has",len(node.cache))
        nodes[idx % node_pershard].add_tx(tx)
    # print("nodes",nodes)
    for node in nodes:
        print("node",node.no,"recieved",len(node.cache),"txs.")
    print("finish send txs")

def test(nodes,N):
    a = time.time()
    gls = []
    for node in nodes:
    #    gl = gevent.spawn(node.mine)
       gl = gevent.spawn(node.mine_onetime)
       gls.append(gl)
    gevent.joinall(gls)
    b = time.time()
    total_load = sum([node.load for node in nodes])
    print("process ",len(transactions),"transactions cost",b-a,'seconds. shard:',shard_number,"total nodes:",N,"average load is",total_load/N/8192,"MB")

if __name__ == "__main__":
    config = None
    with open('test_node.yaml','r') as file:
        config = yaml.safe_load(file)
        
    N = config['common']['N'] # 节点总数
    shard_no =int( sys.argv[1] ) # 2 3 4  分片序号
    txs_per_node = config['test']['txs_per_node']  # 每个节点处理多少交易
    shard_number = config['common']['shard_numbers'] # 分片总数
    B = config['test']['B'] # tx pool batch
    node_pershard = config['common']['nodes_per_shard'] # 每个分片几个节点
    stringlength = 167 # 交易载荷长度
    start_no = (shard_no-1) * node_pershard
    end_no = (shard_no) * node_pershard - 1
    cross_proportion = config['test']['cross_proportion']
    print("----------------test Node ----------------")
    transactions = generateTransactions( node_pershard * txs_per_node ,cross_proportion)
    nodes = get_nodes(shard_no, start_no, end_no, B)
    send_txs(nodes, transactions)
    input("输入任意字符开始进行共识")
    print("开始共识")
    test(nodes,N)
    print("finish")
