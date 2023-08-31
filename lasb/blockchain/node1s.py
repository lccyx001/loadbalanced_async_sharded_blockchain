from loadbalanced_async_sharded_blockchain.lasb.blockchain.server import Server,run_forever

if __name__ == "__main__":
    run_forever(Server("node1","127.0.0.1","4001"))