import zerorpc
from honeybadger import HoneyBadgerBFT
from config import Config
import gevent
from rpcbase import RPCBase

def get_clients():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:{}000".format(i+2))
        clients.append(client)
    return clients

def test_honeybader(clients,N=4):
    greenlets = [None] * N
    badgers = [None] * N

    sid = "SIDA"
    for pid in range(N):
        cfg = Config(pid)
        badgers[pid] = HoneyBadgerBFT(sid,pid,1,cfg.N,cfg.f,cfg.PK,cfg.SK,cfg.ePK,cfg.eSK,clients[pid])
        print("setup badger",pid)

    for pid in range(N):
        tx = "<[ACS Input {}]>".format(pid)
        badgers[pid].submit_tx(tx)
    for pid in range(N):
        tx = "<[ACS Input {}]>".format(pid+10)
        badgers[pid].submit_tx(tx)
    for pid in range(N):
        tx = "<[ACS Input {}]>".format(pid+20)
        badgers[pid].submit_tx(tx)
    print("input tx to badgers")

    
    for i in range(N):    
        greenlets[i] = gevent.spawn(badgers[i].run)

    outs = [greenlets[i].get() for i in range(N)]
    print("receive message")
    for o in outs:
        print(o)

def _make_rpcs(cfg:Config):
    port = cfg.port
    channel = cfg.channels
    host = cfg.host
    rpc = RPCBase(channel,host,port,cfg.N,cfg.id)
    return gevent.spawn(rpc.run_forever),rpc

def run():
    gls = []
    for i in range(4):
        cfg = Config(i)
        servers,rpc = _make_rpcs(cfg)
        gls.append(servers)
        gls.append(gevent.spawn(rpc.connect_broadcast_channel)) 

if __name__ == "__main__":
    run()
    clients = get_clients()
    test_honeybader(clients,4)
    # cfg = Config(0)
    # _make_honeybadger("sida",0,4,1,cfg.PK,cfg.SK,cfg.ePK,cfg.eSK,clients[0])
    # print(clients)
