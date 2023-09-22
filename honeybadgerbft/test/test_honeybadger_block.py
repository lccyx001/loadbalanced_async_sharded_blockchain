from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.honeybadgerbft.binaryagreement import binaryagreement
from loadbalanced_async_sharded_blockchain.honeybadgerbft.reliablebroadcast import reliablebroadcast
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commonsubset import commonsubset
from loadbalanced_async_sharded_blockchain.honeybadgerbft.honeybadger_block import honeybadger_block
from loadbalanced_async_sharded_blockchain.common.config import Config
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

def _make_honeybadger_block(sid,pid,N,f,PK,SK,ePK,eSK,client):
    def _setup(j):
        # setup coin
        cc_sid = sid + 'COIN' + str(j)
        coin = commoncoin(cc_sid,pid,N,f,PK,SK,client,j)
        
        # setup ba
        ba_sid = sid + "BA" + str(j)
        gevent.spawn(binaryagreement,ba_sid,pid,N,f,coin,client,j)
        
        # setup rbc
        rbc_sid = sid +  "RBC" + str(j)
        gevent.spawn(reliablebroadcast,rbc_sid,pid,N,f,j,client,j)

    for j in range(N):
        _setup(j)
    acs = gevent.spawn(commonsubset,pid,N,f,client)
    return honeybadger_block(pid,N,f,ePK,eSK,acs.get,client)
        

def test_honeybader_block(clients,N=4):
    badger_blocks = [] 
    for i in range(N):
        cfg = Config(i)
        gl = gevent.spawn(_make_honeybadger_block,"SID",cfg.id,cfg.N,cfg.f,cfg.PK,cfg.SK,cfg.ePK,cfg.eSK,clients[i])
        badger_blocks.append(gl) 
        print("setup badger blocks",i)

    for i in range(N):
        msg = "<[HBBFT Input {}]>".format(i)
        clients[i].propose_set(msg)

    print("input message to badgers")
    outs = [badger_blocks[i].get() for i in range(N)]
    print("receive badgers")
    assert outs[0] == outs[1] == outs[2] == outs[3]

if __name__ == "__main__":
    clients = _get_clients()
    test_honeybader_block(clients,4)
