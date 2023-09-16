from loadbalanced_async_sharded_blockchain.blockchain.message import Message

def test_message():
    msg_types = ["transaction","block","wrong"]
    for mt in msg_types:
        message = Message.create(mt,"hello world")
        if mt != "wrong":
            assert message 
        else:
            assert not message 
        

if __name__ == "__main__":
    test_message()