import zerorpc

def make_all_connected():
    client = zerorpc.Client()
    client.connect("tcp://127.0.0.1:4000")
    client.connect_all()
    

    client1 = zerorpc.Client()
    client1.connect("tcp://127.0.0.1:4001")
    client1.connect_all()
    
    client2 = zerorpc.Client()
    client2.connect("tcp://127.0.0.1:4002")
    client2.connect_all()
    return client,client1,client2

def test_commoncoin():
    client, client1, client2 = make_all_connected()
    for round in range(5):
        print("round",round)
        coin1 = client.get_coin(round)
        coin2 = client1.get_coin(round)
        coin3 = client2.get_coin(round)
        print(coin1,coin2,coin3)
        coin1 = client.get_coin(round)
        coin2 = client1.get_coin(round)
        coin3 = client2.get_coin(round)
        print(coin1,coin2,coin3)

if __name__ == "__main__":
    test_commoncoin()
    
    


