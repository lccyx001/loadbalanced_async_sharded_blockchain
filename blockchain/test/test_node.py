from loadbalanced_async_sharded_blockchain.blockchain.core import *
from loadbalanced_async_sharded_blockchain.blockchain.node import Node
import random
from faker import Faker
fake = Faker()

def get_nodes(shard_number, N, B):
    nodes = [Node(i % shard_number, i, B) for i  in range(N)]
    # print("shard:", shard_number, "per shard nodes:", N/shard_number ,)
    # for node in nodes:
    #     print("shard no",node.shard_no)
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
            from_shard = [i % shard_number]
            to_shard = [i % shard_number]
        else:
            if(i/number <= cross_proportion):
                from_shard = [ random.randint(0,shard_number) ]
                to_shard = [ (from_shard[0] +1 ) % shard_number ]
                cross += 1
            else:
                from_shard = to_shard = [i % shard_number]
        payload = generate_random_str(stringlength)
        txs.append(Transaction.new(from_hash,to_hash,from_shard,to_shard,amount,payload))
    print("generate transactions:total:", number, "cross:", cross)
    return txs

def send_txs(nodes, transactions):
    for idx,tx in enumerate(transactions) :
        nodes[idx % N].add_tx(tx)

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
    N = 32
    shard_number = 8
    stringlength = 167
    B = 10000 
    txs_per_node = 256 
    cross_proportion = 0
    print("----------------test Node ----------------")
    transactions = generateTransactions( N * txs_per_node ,cross_proportion)
    nodes = get_nodes(shard_number, N, B)
    send_txs(nodes, transactions)
    test(nodes,N)
    print("finish")
