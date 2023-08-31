import zerorpc
import gevent
import random
import argparse

def make_rbc_all_connected():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:20{}0".format(i))
        client.init_connections()
        clients.append(client)
    return clients

def test_ba():
    parser = argparse.ArgumentParser(description='RBC instance.')
    parser.add_argument('L', help='leader id')
    args = parser.parse_args()
    leader = int(args.L)
    rbcs = make_rbc_all_connected()
    rbcleader = rbcs[leader]
    m = b"Hello! This is a test message."
    rbcleader.reliablebroadcast(m)
    print("finish rbc")
    for party in rbcs:
        print(party.RBCresult())


if __name__ == "__main__":
    # test_commoncoin()
    test_ba()
    


