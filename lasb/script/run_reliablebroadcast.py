import yaml
import argparse
import gevent
from reliablebroadcast import ReliableBroadcast
import random


def _read_args():
    parser = argparse.ArgumentParser(description='RBC instance.')
    parser.add_argument('f', help='config file name')
    args = parser.parse_args()
    return args

def _load_config(args,id):
    with open(args.f,'r') as yf:
        stream = yf.read()
    config = yaml.load(stream,yaml.SafeLoader)
    common_config = config.get("common")
    rbc_config = config.get("rbc").get("server{}".format(id))
    return common_config, rbc_config

def start_rbc_server(common_config,rbc_config,id,leader):
    sid = rbc_config.get("sid")
    pid = rbc_config.get("pid")
    N = common_config.get("N")
    f = common_config.get("f")
    leader = leader
    broadcast_channels = rbc_config.get("broadcast_channels")
    host = rbc_config.get("host")
    port = rbc_config.get("port")
    rbc = ReliableBroadcast(sid,pid,N,f,leader,broadcast_channels)
    gl = gevent.spawn_later(id,rbc.run_forever,host,port)
    return gl

if __name__ == "__main__":
    args = _read_args()
    gls = []
    leader = random.randint(0,3)
    print("leader",leader)
    for id in range(4):
        common_config,rbc_config = _load_config(args,id)
        rbc_gl = start_rbc_server(common_config,rbc_config,id,leader)
        gls.append(rbc_gl)
    gevent.joinall(gls)


    
    
    