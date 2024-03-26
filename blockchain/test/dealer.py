import sys
sys.path.append(r'../../..')
import yaml


def generate_config(N,f,host_array,node_pershard):
    common = {
        "pk":"pk",
        "N":N,
        "f":f,
        "epk":"epk" 
    }
    data = {"common":common,}
    for i in range(N):
        node_key = "node"+str(i)
        data[node_key] = {}
        data[node_key]['host'] = '0.0.0.0'
        data[node_key]['port'] = "20"+str(i%node_pershard)+"1"
        channels = []
        badger_channels = []
        for j,host in enumerate(host_array):
            if i==j:
                continue
            uri = "tcp://"+host+":20"+str( j % node_pershard )+"1"
            channels.append([j,uri])
            
            badger_uri = "tcp://"+host+":20"+str( j % node_pershard )+"0"
            badger_channels.append([j,badger_uri])
        data[node_key]['channels'] = channels
        honeybadger = {
            "host":'0.0.0.0',
            "port":"20"+str(i%node_pershard)+"0",
            "channels":badger_channels
        }
        data[node_key]["honeybadger"] = honeybadger
    with open('./config.yaml','w',encoding='utf-8') as f:
        yaml.dump(data, stream=f, allow_unicode=True)
    print("generate yaml config success")
    
def generate_sign_secret(N,f):
    from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshsig.boldyreva import dealer
    PK, SKs = dealer(N, f+1)  

    data =PK.serialize()
    # print(data)
    # print(data)
    with open("pk",'wb')as f:
        f.write(data)
    with open("pk",'rb') as f:
        data = f.read()
    obj_dict = PK.deserialize(data)
    # print(obj_dict)
    # print("******************")

    for idx,sk in enumerate(SKs):
        data =sk.serialize()
        # print(data)
        # print(data)
        with open("sk{}".format(idx),"wb")as f:
            f.write(data)
        with open("sk{}".format(idx),"rb") as f:
            data = f.read()
        obj_dict = sk.deserialize(data)
        # print(obj_dict)
        # print("####################")
    print("generate secret keys success.")
    
def generate_enc_secret(N,f):
    from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto import threshenc as tpke
    dealer = tpke.dealer
    PK, SKs = dealer(N, f+1)  

    data =PK.serialize()
    # print(data)
    # print(data)
    with open("epk",'wb')as f:
        f.write(data)
    with open("epk",'rb') as f:
        data = f.read()
    obj_dict = PK.deserialize(data)
    # print(obj_dict)
    # print("******************")

    for idx,sk in enumerate(SKs):
        data =sk.serialize()
        # print(data)
        # print(data)
        with open("esk{}".format(idx),"wb")as f:
            f.write(data)
        with open("esk{}".format(idx),"rb") as f:
            data = f.read()
        obj_dict = sk.deserialize(data)
        # print(obj_dict)
        # print("####################")
    print("generate enc secret keys success.")

if __name__ == "__main__":
    config = None
    with open('test_node.yaml','r') as file:
        config = yaml.safe_load(file)
    N , f , node_pershard= config['common']['N'], config['dealer']['f'], config['common']['nodes_per_shard']
    
    shard_hosts = config['dealer'][sys.argv[1]]
    host_array = []
    for shard_host in shard_hosts:
        host_array += [shard_host] * node_pershard
    generate_config(N,f,host_array,node_pershard)
    if len(sys.argv)>2:
        generate_sign_secret(N,f)
        generate_enc_secret(N,f)
    
    
    

