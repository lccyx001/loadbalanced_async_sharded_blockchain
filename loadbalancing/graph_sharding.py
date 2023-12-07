import time
import networkx as nx
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import json
# import sklearn
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans

def graph_sharding(cursor,conn,shard,totals,pre_handler=True):
    if pre_handler:
        data_pre_handler(cursor,conn,totals)
    _calculate_sharding(cursor,conn,shard)
    _apply_sharding_result(cursor,conn,totals)

def data_pre_handler(cursor,conn,totals):
    _extract_to_graph_tx(cursor,conn,totals)
    _extract_to_graph_tx_distinct(cursor,conn)
    _build_id_hash_str_map(cursor,conn)

def _calculate_sharding(cursor,conn,shard=4):
    matrix = _build_adjacency_matrix(cursor,conn)
    matrix = _get_simility_matrix(matrix)
    labels = _kmeanspp(matrix,shard)
    _sharding(cursor,conn,labels,0)

def _extract_to_graph_tx(cursor,conn,totals):
    offset = 0
    limit = 1000
    while offset < totals:
        start = time.time()
        res = _get_batch_transactions(cursor,offset,limit)
        if not len(res):
            break
        datas = _get_user_tx_times(res)
        _write_to_graph_tx(cursor,datas,conn)
        offset += limit
        end =  time.time()
        print("_extract_to_graph_tx offset",offset,"costs:",end - start)

def _get_batch_transactions(cursor,offset,limit):
    query_sql = "SELECT `transactionHash`, `from`, `to`, `value` FROM transactions LIMIT {offset}, {limit};"
    cursor.execute(query_sql.format(offset=offset,limit=limit))
    res = cursor.fetchall()
    return res

# 用户交易次数求和
def _get_user_tx_times(batch):
    user_tx_map = {}
    for idx, row in enumerate(batch):
        from_hash = row[1]
        to_hash = row[2]
        if from_hash == 'None' or to_hash == 'None':
                continue
        first = from_hash if from_hash > to_hash else to_hash
        second = from_hash if from_hash <= to_hash else to_hash
        key = "%s_%s" % (first,second) 
        if not user_tx_map.get(key):
            user_tx_map[key] =  1
            continue

        user_tx_map[key] += 1

    datas = [(key.split('_')[0], key.split('_')[1], value) for key, value in user_tx_map.items()]
    return datas

def _write_to_graph_tx(cursor,datas,conn):
    sql = "INSERT INTO graph_tx (`txone`, `txtwo`, `tx_times`) VALUES (%s, %s, %s)"  
    cursor.executemany(sql,datas)
    conn.commit()

def _extract_to_graph_tx_distinct(cursor,conn):
    offset = 0
    limit = 1000
    while True:
        s = time.time()
        query_sql = "SELECT txone,txtwo,SUM(tx_times) t  from graph_tx GROUP BY txone,txtwo ORDER BY t LIMIT {offset}, {limit};"
        cursor.execute(query_sql.format(offset=offset,limit=limit))
        res = cursor.fetchall()
        if not len(res):
            break
        datas = []
        for idx, row in enumerate(res):
            one = row[0]
            two = row[1]
            t = row[2]
            datas.append([one,two,t])
        _write_to_graph_tx_distinct(cursor,datas,conn)
        offset += limit
        e = time.time()
        print("extract_to_graph_tx_distinct:offset:{} costs:{}".format(offset,e-s))

def _write_to_graph_tx_distinct(cursor,datas,conn):
    sql = "INSERT INTO graph_tx_distinct (`txone`, `txtwo`, `tx_times`) VALUES (%s, %s, %s)"  
    cursor.executemany(sql,datas)
    conn.commit()

def _build_id_hash_str_map(cursor,conn):
    a = time.time()
    query_sql = "SELECT txone,txtwo,tx_times from graph_tx_distinct;"
    cursor.execute(query_sql)
    res = cursor.fetchall()
    user_set = set()
    for row in res:
        user_set.add(row[0])
        user_set.add(row[1])

    batch = []
    insert_sql = "INSERT INTO graph_user_hash (`hashstr`) VALUES (%s)"

    for hashstr in user_set:
        if len(batch) >2000:
            cursor.executemany(insert_sql,batch)
            conn.commit()
            batch = []
        batch.append(hashstr)
    else:
        if len(batch)>0:
            cursor.executemany(insert_sql,batch)
            conn.commit()
    b = time.time()
    print("build_id_hash_str_map cost:",b-a)

def _get_user_map(cursor, shard=False):
    a =  time.time()
    user_map_sql = "SELECT id,hashstr from graph_user_hash ;"
    if shard:
        user_map_sql = "SELECT id,hashstr,shard from graph_user_hash where shard is not NULL;"

    cursor.execute(user_map_sql)
    user_map = {}
    res_map = cursor.fetchall()
    for record in res_map:
        if shard:
            user_map[record[1]] = record[2]
        else:
            user_map[record[1]] = record[0]
    b = time.time()
    print("construct map",b-a)
    return user_map

def _build_adjacency_matrix(cursor,conn,limit=10000):
    user_map = _get_user_map(cursor)
    a = time.time()
    query_sql = "SELECT txone,txtwo,tx_times from graph_tx_distinct;"
    # query_sql = "SELECT txone,txtwo,tx_times from graph_tx_distinct LIMIT 0,{limit};".format(limit=limit)
    cursor.execute(query_sql)
    res = cursor.fetchall()
    G = nx.Graph()
    for row in res:
        aid = user_map.get(row[0])
        bid = user_map.get(row[1])
        G.add_edge(aid,bid,weight=row[2])

    # adjacency_matrix = nx.to_scipy_sparse_matrix(G, format='csr') 
    adjacency_matrix = nx.adjacency_matrix(G) 
    b = time.time()
    print("build_adjacency_matrix costs:", b-a )
    return adjacency_matrix

def _get_simility_matrix(adjacency_matrix):
    a = time.time()
    csr_adj_matrix = csr_matrix(adjacency_matrix)
    csr_trans_matrix = csr_matrix(adjacency_matrix.transpose())
    simility_matrix = cosine_similarity(csr_adj_matrix,csr_trans_matrix)
    print("total user",len(simility_matrix))
    b = time.time()
    print("get_simility_matrix cost", b-a, "seconds")
    return simility_matrix


def _kmeanspp(matrix,k):
    a = time.time()
    kmeans = KMeans(n_clusters=k,init="k-means++",random_state=42)
    kmeans.fit(matrix)
    labels = kmeans.labels_
    centroids = kmeans.cluster_centers_
    # print("labels",labels)
    print("labels length",len(labels))
    # print("centroids",centroids)
    b = time.time()
    print("kmeans costs:",b-a)
    return labels

def _sharding(cursor,conn,labels,offset=0):
    cursor.execute("select min(id) from graph_user_hash;")
    idstart = cursor.fetchone()[0]
    a = time.time()
    update_sql = "update graph_user_hash set `shard`=%s where id=%s"
    data = []
    for id,shard in enumerate(labels):
        if len(data)>100:
            cursor.executemany(update_sql,data)
            conn.commit()
            data = []
        data.append((shard,id+offset+idstart,))
    else:
        if(len(data))>0:
            cursor.executemany(update_sql,data)
            conn.commit()
    b= time.time()
    print("update sharding costs:",b-a)



def _apply_sharding_result(cursor,conn,totals):
    a = time.time()
    user_map = _get_user_map(cursor,shard=True)
    offset = 0
    limit = 1000
    data = []
    while offset<totals:
        start = time.time()
        res = _get_batch_transactions(cursor,offset,limit)
        if not len(res):
            break
        
        for row in res:
            if len(data)>100:
                sql =  "INSERT INTO graph_sharding (`transactionHash`, `from`, `to`, `value`,`from_shard`,`to_shard`,`cross`) VALUES (%s, %s, %s, %s, %s, %s, %s)" 
                cursor.executemany(sql,data)
                conn.commit()
                data = []
                
            tx_hahsh = row[0]
            value = row[3]
            from_hash = row[1]
            to_hash = row[2]
            if from_hash == 'None' or to_hash == 'None':
                continue
            from_shard= user_map.get(from_hash)
            to_shard = user_map.get(to_hash)
            if not from_shard or not to_shard:
                continue
            cross = 1 if from_shard != to_shard else 0 
            data.append([tx_hahsh,from_hash,to_hash,value,from_shard,to_shard,cross])
        offset += limit
        end = time.time()
        print("scan to ",offset,"costs:",end-start)

    if len(data)>0:
        sql =  "INSERT INTO graph_sharding (`transactionHash`, `from`, `to`, `value`,`from_shard`,`to_shard`,`cross`) VALUES (%s, %s, %s, %s, %s, %s, %s)" 
        cursor.executemany(sql,data)
        conn.commit()
        data = [] 
        
    z = time.time()
    print("apply_sharding_result costs:",z-a)
        
        


def _compare_two_matrix(matrix1,matrix2):
    for ridx, row in enumerate(matrix1) :
        for cidx,col in enumerate(row):
            if col!=matrix2[ridx][cidx]:
                return False 
    return True