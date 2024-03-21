from loadbalanced_async_sharded_blockchain.blockchain.core import *

if __name__ == "__main__":
    print("----------------test transaction----------------")
    data = {"from_hash":"0x11","to_hash":"0x12","amount":10}
    tx = Transaction.new(data["from_hash"],data["to_hash"],1,2,100,"something payload")
    print("success")

    print("----------------test UserTree----------------")
    user_tree = UserTree()
    user_hash = "user1hash"
    user_tree.add_user(user_hash,100)
    user_tree.update_user(user_hash,20)
    assert user_tree.get_balance(user_hash) == 20
    print("success")
    
    print("----------------test Block----------------")
    block = Block.new(0,"Genies block hash",[tx],[1,2])
    print(block)
    print("success",)
    
    print("----------------test Blockchain----------------")
    bc = BlockChain(1)
    bc.append(block)
    ledger = bc.get_ledger()
    print(ledger)
    assert len(ledger) == 1
    print("success")
    
    
    
    