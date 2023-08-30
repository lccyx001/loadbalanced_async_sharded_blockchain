import zerorpc
import gevent
import random

def make_cc_all_connected():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:40{}0".format(i))
        client.connect_all()
        clients.append(client)
    
    return clients

def make_ba_all_connected():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:40{}1".format(i))
        client.init_connections()
        clients.append(client)
    return clients

def test_ba():
    ccs = make_cc_all_connected()
    bas = make_ba_all_connected()
    gls = []
    for i,ba in enumerate(bas):
        randint = random.randint(0,1)
        print(randint)
        gl = gevent.spawn_later(i+1,ba.binaryagreement,randint)
        gls.append(gl)
    gevent.joinall(gls)
    print([gl.value for gl in gls])


if __name__ == "__main__":
    # test_commoncoin()
    test_ba()
    


