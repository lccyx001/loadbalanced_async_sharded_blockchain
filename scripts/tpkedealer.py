import sys
sys.path.append(r'..')
from honeybadgerbft.crypto import threshenc as tpke
# import json
# import pickle
dealer = tpke.dealer

if __name__ == "__main__":
    N , f = 4, 1
    PK, SKs = dealer(N, f+1)  

    data =PK.serialize()
    # print(data)
    print(data)
    with open("epk",'wb')as f:
        f.write(data)
    with open("epk",'rb') as f:
        data = f.read()
    obj_dict = PK.deserialize(data)
    print(obj_dict)
    print("******************")

    for idx,sk in enumerate(SKs):
        data =sk.serialize()
        # print(data)
        print(data)
        with open("esk{}".format(idx),"wb")as f:
            f.write(data)
        with open("esk{}".format(idx),"rb") as f:
            data = f.read()
        obj_dict = sk.deserialize(data)
        print(obj_dict)
        print("####################")


