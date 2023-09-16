from honeybadger import HoneyBadgerBFT
import gevent
import json

def test_honeybader(N=4):
    greenlets = [None] * N
    badgers = [None] * N



    sid = "SIDA"
    for pid in range(N):
        tx = json.dumps(["<[ACS Input {}]>".format(pid) * 4]) 
        badgers[pid] = HoneyBadgerBFT(sid,pid,tx)
        print("setup badger",pid)
    
    for i in range(N):    
        greenlets[i] = gevent.spawn(badgers[i].run)

    outs = [greenlets[i].get() for i in range(N)]
    print("receive message")
    for o in outs:
        print(o)

if __name__ == "__main__":
    test_honeybader(4)
