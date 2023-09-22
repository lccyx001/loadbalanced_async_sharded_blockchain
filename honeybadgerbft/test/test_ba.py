from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
from loadbalanced_async_sharded_blockchain.honeybadgerbft.binaryagreement import binaryagreement
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.common.config import Config
import random
import gevent

def _get_clients():
    clients = []
    for i in range(4):
        config = Config(i)
        client = ClientBase(config.honeybadger_channels,config.honeybadger_host,config.honeybadger_port,config.N,config.id)
        gevent.spawn(client.run_forever)
        gevent.spawn(client.connect_broadcast_channel)
        clients.append(client)
    return clients

def _dummy_ba_input(clients,vi,special=False):
    j = 0 
    for i, client in enumerate(clients) :
        # vi = random.randint(0,1)
        if special:
            vi = i % 2
        client.aba_in(vi,j)
        

def _make_bas(clients):
    bagls = []
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
        ba = gevent.spawn(binaryagreement,sid,pid,N,f,cc,clients[i],j)
        bagls.append(ba)
    return bagls

def test_ba():
    clients = _get_clients()
    j = 0

    vi = 0
    bas = _make_bas(clients)
    _dummy_ba_input(clients,vi)
    gevent.joinall(bas)
    result = [_.aba_out(j) for _ in clients]
    assert result[0] == result[1] == result[2] == result[3] == 0

    for cli in clients:
        cli.reset()
    vi = 1
    bas = _make_bas(clients)
    _dummy_ba_input(clients,vi)
    gevent.joinall(bas)
    result = [_.aba_out(j) for _ in clients]
    assert result[0] == result[1] == result[2] == result[3] == 1

    for cli in clients:
        cli.reset()
    bas = _make_bas(clients)
    _dummy_ba_input(clients,vi,special=True)
    gevent.joinall(bas)
    result = [_.aba_out(j) for _ in clients]
    assert result[0] == result[1] == result[2] == result[3]
    

if __name__ == "__main__":
    test_ba()
    
    


