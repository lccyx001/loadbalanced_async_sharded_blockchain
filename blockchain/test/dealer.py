import sys
sys.path.append(r'..')
import yaml
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshsig.boldyreva import dealer
# import json
# import pickle

def generate_config(N,f):
    host_array = ['127.0.0.1'] * N
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
        data[node_key]['host'] = host_array[i]
        data[node_key]['port'] = str(2+int(i/10))+str(i%10)+"01"
        channels = []
        badger_channels = []
        for j,host in enumerate(host_array):
            if i==j:
                continue
            uri = "tcp://"+host+":"+str(2+int(j/10))+str( (j)%10 )+"01"
            channels.append([j,uri])
            
            badger_uri = "tcp://"+host+":"+str(2+int(j/10))+str( (j)%10 )+"00"
            badger_channels.append([j,badger_uri])
        data[node_key]['channels'] = channels
        honeybadger = {
            "host":host_array[i],
            "port":str(2+int(i/10))+str(i%10)+"00",
            "channels":badger_channels
        }
        data[node_key]["honeybadger"] = honeybadger
    print(data)
    with open('./config.yaml','w',encoding='utf-8') as f:
        yaml.dump(data,stream=f,allow_unicode=True)
    


# if __name__ == "__main__":
    
#     

if __name__ == "__main__":
    N , f = 4, 1
    generate_config(N,f)
    print("generate yaml config success")
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
    
    

