import zerorpc
import random
from reliablebroadcast import reliablebroadcast
import gevent
from loadbalanced_async_sharded_blockchain.common.config import Config

def get_clients():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:{}000".format(i+2))
        clients.append(client)
    return clients

def run(rbcclients):
    leader = random.randint(0,3)
    print("leader",leader)
    gls = []
    for i in range(4):
        cfg = Config(i)
        sid = "sidA"
        input = rbcclients[i].input_rbc if i == leader else None
        j = 0 
        gl = gevent.spawn(reliablebroadcast,sid, i ,cfg.N,cfg.f,leader,rbcclients[i],j)
        gls.append(gl)
    m = b"hello! this is a test message."
    rbcclients[leader].input_rbc_insert(m)
    gevent.joinall(gls)
    result = [t.value for t in gls]
    print(result)
    for r in result:
        assert r == m
    print("ok")


if __name__ == "__main__":
    clients = get_clients()
    run(clients)
    


