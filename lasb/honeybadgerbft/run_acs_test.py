import zerorpc
from binaryagreement import binaryagreement
from commoncoin import commoncoin
from reliablebroadcast import reliablebroadcast
from commonsubset import commonsubset
from config import Config
import gevent

def get_clients():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:{}000".format(i+2))
        clients.append(client)
    return clients

def _make_acs(sid,pid,N,f,PK,SK,client):
    greenlets = []
    def _setup(j):
        # setup coin
        cc_sid = sid + 'COIN' + str(j)
        coin = commoncoin(cc_sid,pid,N,f,PK,SK,client.broadcast_cc,client.receive_cc,j)
        print("setup cc",pid,j)
        # setup ba

        ba_sid = sid + "BA" + str(j)
        ba = gevent.spawn(binaryagreement,ba_sid,pid,N,f,coin,
                        client.input_ba,
                        client.output_ba,
                        client.broadcast_ba,
                        client.receive_ba, 
                        j)
        print("setup ba",pid,j)

        # setup rbc
        rbc_sid = sid +  "RBC" + str(j)
        input = client.input_rbc if j == pid else None 
        # 
        rbc = gevent.spawn(reliablebroadcast,rbc_sid,pid,N,f,j,
                            input,
                            client.receive_rbc,
                            client.send_rbc,
                            client.broadcast_rbc,
                            client.rbc_in,
                            j)
        print("setup rbc",pid,j,"input",input)
        greenlets.extend([ba,rbc])

    for j in range(N):
        _setup(j)

    return commonsubset(pid,N,f,client.rbc_out,client.aba_in,client.aba_out)

def test_acs(clients,N=4):
    # for i in range(4):
    #     client = clients[i]
    #     m = "<[ACS Input {}]>".format(i)
    #     client.input_rbc_insert(m)
    #     gevent.sleep(2)
    # outs = [threads[i].get() for i in range(4)]
    # print("result",outs)
    acs_greenlets = [None] * N
    for i in range(N):
        cfg = Config(i)
        acs_greenlets[i] = gevent.spawn(_make_acs,"SID",cfg.id,cfg.N,cfg.f,cfg.PK,cfg.SK,clients[i])
        print("setup acs",i)
    print("setup acs")

    for i in range(N):
        print("input message",i)
        clients[i].input_rbc_insert("<[ACS Input {}]>".format(i))
        gevent.sleep(5)
    print("input message to acs")
    outs = [acs_greenlets[i].get() for i in range(N)]
    print(outs)
    

if __name__ == "__main__":
    clients = get_clients()
    # TODO: 最后一个消息没有打印出来
    test_acs(clients,4)
    
    


