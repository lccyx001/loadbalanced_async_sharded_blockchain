
from commoncoin import CommonCoin
from crypto.threshsig.boldyreva import dealer,TBLSPublicKey,TBLSPrivateKey
import yaml
import argparse

def read_args():
    parser = argparse.ArgumentParser(description='commoncoin instance.')
    parser.add_argument('id', help='instance id, start from 0')
    parser.add_argument('f', help='config file name')
    args = parser.parse_args()
    return args

def read_config():
    with open(args.f,'r') as yf:
        stream = yf.read()
    config = yaml.load(stream,yaml.SafeLoader)
    config = config.get("commoncoin")
    local_config = config.get("server{}".format(args.id))
    return config,local_config

def load_keys(config,local_config):
    with open(config.get("pk"),"rb") as f:
        pk = f.read()
    pk = TBLSPublicKey.deserialize(pk)
    public_key = TBLSPublicKey.from_dict(pk)

    with open(local_config.get("sk"),"rb") as f:
        sk = f.read()
    sk = TBLSPrivateKey.deserialize(sk)
    private_key = TBLSPrivateKey.from_dict(sk)
    return public_key,private_key


if __name__ == "__main__":
    args = read_args()
    config, local_config = read_config()
    pk,sk = load_keys(config,local_config)
    cc = CommonCoin(config.get("instance_id"),
                    local_config.get("id"),
                    config.get("N"),
                    config.get("f"),
                    pk,
                    sk,
                    local_config.get("channels"))
    cc.run_forever(local_config.get("host"),local_config.get("port"))
