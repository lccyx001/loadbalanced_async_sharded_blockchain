from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
from loadbalanced_async_sharded_blockchain.honeybadgerbft.binaryagreement import binaryagreement
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.honeybadgerbft.reliablebroadcast import reliablebroadcast
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commonsubset import commonsubset
from loadbalanced_async_sharded_blockchain.common.config import Config
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

def _make_acs(sid,pid,N,f,PK,SK,client):
    
    def _setup(j):
        # setup coin
        cc_sid = sid + 'COIN' + str(j)
        coin = commoncoin(cc_sid,pid,N,f,PK,SK,client,j)

        # setup ba
        ba_sid = sid + "BA" + str(j)
        ba = gevent.spawn(binaryagreement,ba_sid,pid,N,f,coin,client,j)

        # setup rbc
        rbc_sid = sid +  "RBC" + str(j)
        rbc = gevent.spawn(reliablebroadcast,rbc_sid,pid,N,f,j,client,j)
        
        

    for j in range(N):
        _setup(j)

    return commonsubset(pid,N,f,client)

def test_acs(clients,N=4):
    acs_greenlets = [] 
    for i in range(N):
        cfg = Config(i)
        gl = gevent.spawn(_make_acs,"SID",cfg.id,cfg.N,cfg.f,cfg.PK,cfg.SK,clients[i])
        acs_greenlets.append(gl)  
    print("setup acs")
    
    for i in range(N):
        msg = "<[ACS Input {}]>".format(i)
        print("msg",msg)
        clients[i].acs_in(msg)
    print("input message to acs")
    
    outs = [acs_greenlets[i].get() for i in range(N)]
    print("receive message")
    assert outs[0] == outs[1] == outs[2] == outs[3]

    print("ok")
        

if __name__ == "__main__":
    clients = get_clients()
    test_acs(clients,4)
