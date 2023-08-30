import yaml
import argparse
import gevent
from binaryagreement import Binaryagreement
from commoncoin import CommonCoin
from crypto.threshsig.boldyreva import TBLSPublicKey,TBLSPrivateKey
import yaml

def _read_args():
    parser = argparse.ArgumentParser(description='binaryagreement instance.')
    parser.add_argument('f', help='config file name')
    args = parser.parse_args()
    return args

def _load_config(args,id):
    with open(args.f,'r') as yf:
        stream = yf.read()
    config = yaml.load(stream,yaml.SafeLoader)
    common_config = config.get("common")
    cc_config = config.get("commoncoin")
    ba_config = config.get("binaryaggrement").get("server{}".format(id))
    return common_config, cc_config, ba_config

def _start_commoncoin(id, cc_config, common_config):
    N = common_config.get("N")
    f = common_config.get("f")
    
    with open(common_config.get("public_key"),"rb") as fd:
        pk = fd.read()
    pk = TBLSPublicKey.deserialize(pk)
    public_key = TBLSPublicKey.from_dict(pk)

    with open(common_config.get("private_keys")[int(id)],"rb") as fd:
        sk = fd.read()
    sk = TBLSPrivateKey.deserialize(sk)
    private_key = TBLSPrivateKey.from_dict(sk)

    instance_id = cc_config.get("instance_id")
    
    local_config = cc_config.get("server{}".format(id))
    local_id = local_config.get("id")
    broadcast_channels = local_config.get("channels")
    cc = CommonCoin(instance_id,local_id,N,f,public_key,private_key,
                 broadcast_channels)
    host ,port = local_config.get("host"),local_config.get("port")
    gl = gevent.spawn(cc.run_forever,host,port)
    return gl

def _start_binaryagreement(common_config,ba_config):
    session_id = ba_config.get("session_id")
    local_id = ba_config.get("localid")
    N = common_config.get("N")
    f = common_config.get("f")
    coin_rpc = ba_config.get("coin_rpc")
    host, port = ba_config.get("host"), ba_config.get("port")

    broadcast_channels = ba_config.get("broadcast_channels")
    ba = Binaryagreement(
        session_id,
        local_id,
        N,f,
        coin_rpc,
        broadcast_channels
    )
    return gevent.spawn(ba.run_forever,host,port)

if __name__ == "__main__":
    args = _read_args()
    gls = []
    for id in range(4):
        common_config, cc_config, ba_config = _load_config(args,id)
        cc_greenlet = _start_commoncoin(id,cc_config,common_config)
        gls.append(cc_greenlet)
        ba_greenlet = _start_binaryagreement(common_config, ba_config)
        gls.append(ba_greenlet)
    # cc_greenlet.join()
    gevent.joinall(gls)
    
    