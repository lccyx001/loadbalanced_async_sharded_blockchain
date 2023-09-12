import zerorpc
from commoncoin import commoncoin
from binaryagreement import binaryagreement
from reliablebroadcast import reliablebroadcast
from commonsubset import commonsubset
from honeybadger_block import honeybadger_block
from config import Config
import gevent

def get_clients():
    clients = []
    for i in range(4):
        client = zerorpc.Client()
        client.connect("tcp://127.0.0.1:{}000".format(i+2))
        clients.append(client)
    return clients

def _make_honeybadger(sid,pid,N,f,PK,SK,ePK,eSK,client):
    def _setup(j):
        # setup coin
        cc_sid = sid + 'COIN' + str(j)
        coin = commoncoin(cc_sid,pid,N,f,PK,SK,client,j)
        print("setup cc",pid,j)
        # setup ba

        ba_sid = sid + "BA" + str(j)
        
        ba = gevent.spawn(binaryagreement,ba_sid,pid,N,f,coin,client,j)
        print("setup ba",pid,j)

        # setup rbc
        rbc_sid = sid +  "RBC" + str(j)
        input = client.input_rbc if j == pid else None 
        # 
        rbc = gevent.spawn(reliablebroadcast,rbc_sid,pid,N,f,j,input,client,j)
        print("setup rbc",pid,j,"input",input)
    

    for j in range(N):
        _setup(j)
    acs = gevent.spawn(commonsubset,pid,N,f,client.rbc_out,client.aba_in,client.aba_out)
    return honeybadger_block(pid,N,f,ePK,eSK,acs.get,client)
        

def test_honeybader(clients,N=4):
    badgers = [None] * N
    for i in range(N):
        cfg = Config(i)
        badgers[i] = gevent.spawn(_make_honeybadger,"SID",cfg.id,cfg.N,cfg.f,cfg.PK,cfg.SK,cfg.ePK,cfg.eSK,clients[i])
        print("setup badgers",i)

    for i in range(N):
        # if i ==1:
        #     continue
        msg = "<[HBBFT Input {}]>".format(i)
        print("input message",msg)
        clients[i].propose_set(msg)
        # gevent.sleep(5)
    print("input message to badgers")
    outs = [badgers[i].get() for i in range(N)]
    print("receive badgers")
    for o in outs:
        print(o)
    

if __name__ == "__main__":
    clients = get_clients()
    test_honeybader(clients,4)
    # cfg = Config(0)
    # _make_honeybadger("sida",0,4,1,cfg.PK,cfg.SK,cfg.ePK,cfg.eSK,clients[0])
    # print(clients)
    
    


