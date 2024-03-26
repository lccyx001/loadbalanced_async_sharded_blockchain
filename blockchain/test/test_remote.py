import sys
sys.path.append(r'../../..')

from loadbalanced_async_sharded_blockchain.common.rpcbase import RPCBase

server_host = "172.19.18.8"
local_host = "0.0.0.0"
port = "2000"


def run_server():
    broadcast_channels = []
    rpc = RPCBase(broadcast_channels,local_host,port)
    rpc.run_forever()

def run_client():
    broadcast_channels =[[0,"tcp://" + server_host + ":" + port]]
    rpc = RPCBase(broadcast_channels,local_host,port)
    rpc.connect_broadcast_channel()
    client = rpc.remote_channels.get(0)[1]
    print(client)
    print("connect success",client.echo())

if __name__ == "__main__":
    if sys.argv[1] == "s":
        run_server()
    else:
        run_client()
        
