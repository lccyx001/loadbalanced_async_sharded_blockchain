from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.common.config import Config
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
import gevent

def get_clients():
    clients = []
    for i in range(4):
        cfg = Config(i)
        client = ClientBase(cfg.honeybadger_channels,cfg.honeybadger_host,cfg.honeybadger_port,cfg.N,cfg.id)
        gevent.spawn(client.run_forever)
        gevent.spawn(client.connect_broadcast_channel)
        clients.append(client)
    return clients

def run_cc(clients):
    coins_gls = []
    for i in range(4):
        cfg = Config(i)
        sid = "sid2A" 
        pid = i
        N = cfg.N
        f = cfg.f
        pk = cfg.PK
        sk = cfg.SK
        j = 0
        coins_gls.append(commoncoin(sid,pid,N,f,pk,sk,clients[i],j))
    return coins_gls

def test_commoncoin():
    clients = get_clients()
    coins = run_cc(clients)
    for round in range(6):
        ccgls = []
        j = 0
        for i,coin in enumerate(coins) :
            ccgl = gevent.spawn(coin,round,j)
            ccgls.append(ccgl)
        gevent.joinall(ccgls)
        ccs = [gl.get() for gl in ccgls]
        assert ccs[0] == ccs[1] == ccs[2] == ccs[3]
        
if __name__ == "__main__":
    test_commoncoin()
    
    


