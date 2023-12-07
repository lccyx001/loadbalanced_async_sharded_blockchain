def counting(cursor,conn,tablename="hash_sharding"):
    query_sql = "select count(1) from {}".format(tablename)
    cursor.execute(query_sql)
    total =cursor.fetchall()[0][0]
    
    cursor.execute("select count(1) from {} WHERE `cross` = 1;".format(tablename))
    cross = cursor.fetchall()[0][0]

    print("total txs: %d cross txs: %d, cross percentage %f" % (total, cross, cross/total))