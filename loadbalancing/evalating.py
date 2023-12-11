import numpy as np

def counting(cursor,conn,tablename="hash_sharding",shard=4):
    query_sql = "select count(1) from {}".format(tablename)
    cursor.execute(query_sql)
    total =cursor.fetchall()[0][0]
    
    cursor.execute("select count(1) from {} WHERE `cross` = 1;".format(tablename))
    cross = cursor.fetchall()[0][0]
    print("total txs: %d cross txs: %d, cross percentage %f" % (total, cross, cross/total))

    cursor.execute("SELECT from_shard,`cross`,count(1) from {} GROUP BY from_shard,`cross` ORDER BY from_shard,`cross`;".format(tablename))
    groups = cursor.fetchall()
    loads = {}
    for group in groups:
        if not loads.get(group[0]):
            loads[group[0]] = []
        loads[group[0]].append(int(group[2]))    

    shard_loads = [0] * shard
    for k ,v in loads.items():
        print("shard number:",k,"intro tx:",v[0], "inter tx:",v[1])
        shard_loads[int(k)] = sum(v)

    data = np.array(shard_loads)
    variance = np.std(data)
    print("load Standard Deviation:",variance)
    print()