from loadbalanced_async_sharded_blockchain.blockchain.transaction import Transaction

def test_tx(data):
    tx =  Transaction.new(data)
    print(tx)

if __name__ == "__main__":
    data = {"index":1,"from_hash":"0x11","to_hash":"0x12","amount":10}
    test_tx(data)