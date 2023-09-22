from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
from loadbalanced_async_sharded_blockchain.honeybadgerbft.honeybadger import HoneyBadgerBFT
from loadbalanced_async_sharded_blockchain.common.config import Config
import gevent

def _get_clients():
    clients = []
    for i in range(4):
        config = Config(i)
        client = ClientBase(config.honeybadger_channels,config.honeybadger_host,config.honeybadger_port,config.N,config.id)
        gevent.spawn(client.run_forever)
        gevent.spawn(client.connect_broadcast_channel)
        clients.append(client)
    return clients

def test_honeybader(clients,N=4):
    badgers = []
    for i in range(N):
        badger = HoneyBadgerBFT("sid",i,clients[i])
        badgers.append(badger)
    print("setup badgers")

    loop_times = 3
    for loop in range(loop_times):
        print("round",loop)
        for i in range(N):
            msg = "<[HBBFT Input {} {}]>".format(i,loop)
            badgers[i].submit_txs(msg)

        print("input message to badgers")
        greenlets = [gevent.spawn(badgers[i].run) for i in range(N)]
        gevent.joinall(greenlets)
        outs = [gl.get() for gl in greenlets]
        print("receive badgers")
        assert outs[0] == outs[1] == outs[2] == outs[3]

def test_honeybader_2(clients,N=4):
    loop_times = 3
    for loop in range(loop_times):
        print("loop",loop)
        badgers = []
        for i in range(N):
            badger = HoneyBadgerBFT("sid",i,clients[i])
            msg = "<[HBBFT Input {} {}]>".format(i,loop)
            badger.submit_txs(msg)
            badgers.append(badger)
        print("setup badgers")

        greenlets = [gevent.spawn(badgers[i].run) for i in range(N)]
        gevent.joinall(greenlets)
        outs = [gl.get() for gl in greenlets]
        print("receive badgers")
        assert outs[0] == outs[1] == outs[2] == outs[3]
        for cli in clients:
            cli.reset()

if __name__ == "__main__":
    clients = _get_clients()
    # test_honeybader(clients,4)
    test_honeybader_2(clients,4)
