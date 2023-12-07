import time

def _write_to_db(cursor,conn,data):
    sql = "INSERT INTO hash_sharding (`transactionHash`, `from`, `to`, `value`,`from_shard`,`to_shard`,`cross`) VALUES (%s, %s, %s, %s, %s, %s, %s)"  
    cursor.executemany(sql,data)
    conn.commit()
    
def _get_batch_transactions(cursor,offset,limit):
    query_sql = "SELECT `transactionHash`, `from`, `to`, `value` FROM transactions LIMIT {offset}, {limit};"
    cursor.execute(query_sql.format(offset=offset,limit=limit))
    res = cursor.fetchall()
    return res

def hash_sharding(cursor,conn,shard=4,totals=100000):
    offset = 0
    limit = 1000
    a= time.time()
    while offset < totals:
        start = time.time()
        res = _get_batch_transactions(cursor,offset,limit)
        if not len(res):
            break
        data = _make_sharding(res, shard)
        _write_to_db(cursor,conn,data)
        end = time.time()
        offset += limit
        print("write to ",offset,"costs:",end - start)
    b = time.time()
    print("hash_sharding costs:",b-a)

def _make_sharding(source=[],shard_number=4):
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
            print(e)

        cross = 1 if from_shard != to_shard else 0
        sharding_data.append([tx_hash,from_hash,to_hash,value,from_shard,to_shard,cross])
    return sharding_data
