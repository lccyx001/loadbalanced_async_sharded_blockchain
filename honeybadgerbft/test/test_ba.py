import zerorpc
from binaryagreement import binaryagreement
from commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.common.config import Config
import random
import gevent

def get_clients():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:{}000".format(i+2))
        clients.append(client)
    return clients

def dummy_ba_input(clients):
    j =0 
    for i, client in enumerate(clients) :
        vi = random.randint(0,1)
        # vi = i % 2
        client.insert_input(vi,j)
        print("insert",vi)

def run(clients):
    bas = []
    for i in range(4):
        cfg = Config(i)
        sid = "sidA" 
        pid = i
        N = cfg.N
        f = cfg.f
        pk = cfg.PK
        sk = cfg.SK
        j = 0
        cc = commoncoin(sid,pid,N,f,pk,sk,clients[i],j)
        ba = gevent.spawn_later(i,binaryagreement,sid,pid,N,f,cc,clients[i],j)
        bas.append(ba)
    return bas

def get_aba_values(clients):
    result = []
    j=0
    for client in clients:
        r = client.get_decide(j)
        result.append(r)
    assert len(result) == 4
    assert result[0]==result[1]==result[2]==result[3]
    print(result)

def test_ba():
    clients = get_clients()
    bas = run(clients)
    dummy_ba_input(clients)
    gevent.joinall(bas)
    get_aba_values(clients)

if __name__ == "__main__":
    test_ba()
    
    


