import sys
sys.path.append(r'../../..')

from loadbalanced_async_sharded_blockchain.common.rpcbase import RPCBase

server_host = "172.19.18.8"
server_port = "2001"
client_host = "127.0.0.1"
client_port = "2101"

def run_server():
    broadcast_channels = [[1,"tcp://" + client_host + ":" + client_port ]]
    rpc = RPCBase(broadcast_channels,server_host,server_port)
    rpc.run_forever()

def run_client():
    broadcast_channels =[[0,"tcp://" + server_host + ":" + server_port]]
    rpc = RPCBase(broadcast_channels,client_host,client_port)
    rpc.connect_broadcast_channel()
    print("connect success")

if __name__ == "__main__":
    if sys.argv[1] == "s":
        run_server()
    else:
        run_client()
        
