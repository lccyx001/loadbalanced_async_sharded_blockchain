import sys
sys.path.append(r'..')
from honeybadgerbft.crypto.threshsig.boldyreva import dealer
# import json
# import pickle

if __name__ == "__main__":
    N , f = 3, 1
    PK, SKs = dealer(N, f+1)  

    data =PK.serialize()
    # print(data)
    print(data)
    with open("pk",'wb')as f:
        f.write(data)
    with open("pk",'rb') as f:
        data = f.read()
    obj_dict = PK.deserialize(data)
    print(obj_dict)
    print("******************")

    for idx,sk in enumerate(SKs):
        data =sk.serialize()
        # print(data)
        print(data)
        with open("sk{}".format(idx),"wb")as f:
            f.write(data)
        with open("sk{}".format(idx),"rb") as f:
            data = f.read()
        obj_dict = sk.deserialize(data)
        print(obj_dict)
        print("####################")


