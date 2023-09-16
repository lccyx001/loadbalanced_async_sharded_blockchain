import zerorpc
from commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.common.config import Config
import gevent

def get_clients():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:{}000".format(i+2))
        clients.append(client)
    return clients

def run_cc(clients):
    coins = []
    for i in range(4):
        cfg = Config(i)
        sid = "sid2A" 
        pid = i
        N = cfg.N
        f = cfg.f
        pk = cfg.PK
        sk = cfg.SK
        j = 0
        coins.append(commoncoin(sid,pid,N,f,pk,sk,clients[i],j))
    return coins

def test_commoncoin():
    clients = get_clients()
    coins = run_cc(clients)
    for round in range(6):
        print("round",round)
        ccgls = []
        for i,coin in enumerate(coins) :
            ccgl = gevent.spawn_later(i,coin,round,0)
            ccgls.append(ccgl)
        gevent.joinall(ccgls)
        ccs = []
        for gl in ccgls:
            ccs.append(gl.get()) 
        print("coins",ccs)
        # assert ccs[0] == ccs[1] == ccs[2] == ccs[3]
        
        
            

if __name__ == "__main__":
    test_commoncoin()
    
    


