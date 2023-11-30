def make_sharding(source=[],shard_number=4):
    def _sharding(hash):
        return int(hash,16) % shard_number
    sharding_data = []
    for idx,row in enumerate(source):
        tx_hash = row[0]
        from_hash = row[1]
        to_hash = row[2]
        value = row[3]
        try:
            from_shard = _sharding(from_hash)
            to_shard = _sharding(to_hash)
        except Exception as e:
            if from_hash == 'None' or to_hash == 'None':
                continue
            # print(e)
            # print(from_hash,to_hash,type(to_hash))
            # exit()
            print(e)
        
        cross = 1 if from_shard != to_shard else 0
        sharding_data.append([tx_hash,from_hash,to_hash,value,from_shard,to_shard,cross])
    return sharding_data




if __name__ == "__main__":
    make_sharding()