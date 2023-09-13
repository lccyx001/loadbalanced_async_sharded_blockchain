from honeybadger import HoneyBadgerBFT
import gevent


def test_honeybader(N=4):
    greenlets = [None] * N
    badgers = [None] * N

    sid = "SIDA"
    for pid in range(N):
        badgers[pid] = HoneyBadgerBFT(sid,pid,1)
        print("setup badger",pid)

    for pid in range(N):
        tx = "<[ACS Input {}]>".format(pid)
        badgers[pid].submit_tx(tx)
    for pid in range(N):
        tx = "<[ACS Input {}]>".format(pid+10)
        badgers[pid].submit_tx(tx)
    for pid in range(N):
        tx = "<[ACS Input {}]>".format(pid+20)
        badgers[pid].submit_tx(tx)
    print("input tx to badgers")

    
    for i in range(N):    
        greenlets[i] = gevent.spawn(badgers[i].run)

    outs = [greenlets[i].get() for i in range(N)]
    print("receive message")
    for o in outs:
        print(o)

if __name__ == "__main__":
    test_honeybader(4)
