from rpcbase import RPCBase
from config import Config
import gevent
from commoncoin import commoncoin

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
        gls.append(gevent.spawn_later(1,rpc.connect_broadcast_channel)) 
    gevent.joinall(gls)        

if __name__ == "__main__":
    run()
    
