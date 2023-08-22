from client import Client

if __name__ == "__main__":
    node2 = Client("node2")
    node2.connect("tcp://127.0.0.1:4000")
    node2.network(["tcp://127.0.0.1:4000","tcp://127.0.0.1:4001"])
    # print("*************************forge genesis block*************************")
    # node2.forge_genesis_block()
    # print(node2.shared_ledger)
    
    # print("*************************new tx*************************")
    # node2.new_tx({"from_hash":"123","to_hash":"123","amount":123})
    # print("blockchain local tx",node2.shared_tx)
    
    # print("*************************forge block*************************")
    # node2.forge_block()
    # print(node2.block_chain.local_block)

    # print("*************************honeybadgerbft*************************")
    # node2.honeybadgerbft()
    # print(node2.shared_ledger)

    # print("*************************request add block*************************")
    # print(node2.shared_ledger)
    # node2.request_add_block()
    # print(node2.shared_ledger)