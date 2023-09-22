from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
import random
from loadbalanced_async_sharded_blockchain.honeybadgerbft.reliablebroadcast import reliablebroadcast
import gevent
from loadbalanced_async_sharded_blockchain.common.config import Config

def get_clients():
    clients = []
    for i in range(4):
        cfg = Config(i)
        client = ClientBase(cfg.honeybadger_channels,cfg.honeybadger_host,cfg.honeybadger_port,cfg.N,cfg.id)
        gevent.spawn(client.run_forever)
        gevent.spawn(client.connect_broadcast_channel)
        clients.append(client)
    return clients

def test_rbc(clients):
    leader = random.randint(0,3)
    print("leader",leader)
    gls = []
    for i in range(4):
        cfg = Config(i)
        sid = "sidA"
        j = 0 
        gl = gevent.spawn(reliablebroadcast,sid, i ,cfg.N,cfg.f,leader,clients[i],j)
        gls.append(gl)

    m = b"hello! this is a test message."
    clients[leader].acs_in(m)

    gevent.joinall(gls)
    result = [t.get() for t in gls]
    
    print(result)
    for r in result:
        assert r == m
    print("ok")


if __name__ == "__main__":
    clients = get_clients()
    test_rbc(clients)
    


