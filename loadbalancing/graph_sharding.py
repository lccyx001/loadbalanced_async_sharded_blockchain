import time
import networkx as nx
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import json
# import sklearn
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans,SpectralClustering

def graph_sharding(cursor,conn,shard,totals,pre_handler=True,):
    if pre_handler:
        data_pre_handler(cursor,conn,totals)
    _calculate_sharding(cursor,conn,shard)
    _apply_sharding_result(cursor,conn,totals)
    # _load_balancing(cursor,conn,totals=totals)

def data_pre_handler(cursor,conn,totals):
    _extract_to_graph_tx(cursor,conn,totals)
    _extract_to_graph_tx_distinct(cursor,conn)
    _build_id_hash_str_map(cursor,conn)

def _calculate_sharding(cursor,conn,shard=4):
    matrix = _build_adjacency_matrix(cursor,conn)
    matrix = _get_simility_matrix(matrix)
    # labels = _kmeanspp(matrix,shard)
    labels=_SpectralClustering(matrix,shard)
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

def _SpectralClustering(matrix,k):
    a = time.time()
    spectral_clustering = SpectralClustering(n_clusters=k, affinity='nearest_neighbors', random_state=0)
    labels = spectral_clustering.fit_predict(matrix)
    b = time.time()
    print("_SpectralClustering costs:",b-a)
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
            if from_shard is None or to_shard is None:
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
        
# def _load_balancing(cursor,conn,totals,tilt_threshold=0.05):

#     def _get_current_loads():
#         # 查询统计每个分片上的负载
#         cursor.execute("SELECT from_shard,count(1) from graph_sharding GROUP BY from_shard ORDER BY from_shard;")
#         groups = cursor.fetchall()
#         current_loads = []
#         for group in groups:
#             current_loads.append(group[1])
#         return current_loads

#     def _balance_array(arr):
#         #将数组尽量平衡，并返回迁移方案
#         total = sum(arr)
#         transfer = [] # (from , to, amout)

#         threshold = tilt_threshold * total
#         print("threshold",threshold)
#         while True:
#             if max(arr) - min(arr) < threshold:
#                 break
#             max_idx = arr.index(max(arr))
#             min_idx = arr.index(min(arr))
#             transfer_load = int((max(arr)- min(arr)) / 2)
#             transfer.append([max_idx,min_idx,transfer_load])
#             arr[max_idx] -= transfer_load
#             arr[min_idx] += transfer_load
#         # merage transfer
#         for i,record in enumerate(transfer):
#             for j , b_record in enumerate(transfer):
#                 if (b_record[0]==record[1]):
#                     if(record[2]>b_record[2]):
#                         record[2] -= b_record[2]
#                         b_record[0] = record[0]
#         return arr,transfer
    
#     def migrate_load(transfor_array,threshold=0.1):
#         # 根据merge后的transfor 指定迁移方案，优先迁移片内负载
#         # 片内负载转移完成后，统计失败的片间负载转移
#         for migration in transfor_array:
#             from_shard,to_shard,counting = migration
#             # 迁移交易特别多的人
#             query_vip = """SELECT  `from`,`to`,from_shard,to_shard,`cross`,COUNT(1) t 
#             from graph_sharding GROUP BY `from`,`to`,from_shard,to_shard,`cross` HAVING  from_shard={} AND to_shard={} ORDER BY t desc""".format(from_shard,from_shard)
#             cursor.execute(query_vip)
#             res = cursor.fetchall()
#             need_migrate = set()
#             count = 0
#             for r in res:
#                 from_hash = r[0]
#                 to_hash = r[1]
#                 need_migrate.add(from_hash)
#                 need_migrate.add(to_hash)
#                 count += r[5]
#                 if abs(count-counting)/counting <threshold:
#                     print("count",count,"counting",counting,"condition",abs(count-counting)/counting)
#                     data = []
#                     c = 0
#                     it = list(need_migrate)
#                     print("need update",len(list(it)))
#                     for hashstr in list(it):
#                         data.append([to_shard,hashstr])
#                         if len(data)>100:
#                             cursor.executemany("""UPDATE graph_sharding SET from_shard=%s WHERE `from` = %s;""",data)
#                             cursor.executemany("""UPDATE graph_sharding SET to_shard=%s WHERE `to` = %s;""",data)
#                             conn.commit()
#                             data = []
#                             c+=100
#                             print("execute update",100)
#                     else:
#                         cursor.executemany("""UPDATE graph_sharding SET from_shard=%s WHERE `from` = %s;""",data)
#                         cursor.executemany("""UPDATE graph_sharding SET to_shard=%s WHERE `to` = %s;""",data)
#                         conn.commit()
#                         data = []
#                     break
#             break
#         # pass

#     current_loads = _get_current_loads()    
#     # 设定一个阈值，当其他分片之间的负载倾斜超过这个值，就执行下面的步骤
#     if max(current_loads) - min(current_loads) < tilt_threshold * totals:
#         return
    
#     # 1.计算分片之间互相要转移的系统负载
#     print("before loadbalancing",current_loads,"total",sum(current_loads))
#     balanced_loads,transfor_array = _balance_array(current_loads)
#     print(balanced_loads,"total",sum(balanced_loads))
#     print(transfor_array)
#     # 2. 寻找合适的负载，进行负载迁移
#     # migrate_load(transfor_array, )
#     print("")
#     pass     

def _compare_two_matrix(matrix1,matrix2):
    for ridx, row in enumerate(matrix1) :
        for cidx,col in enumerate(row):
            if col!=matrix2[ridx][cidx]:
                return False 
    return True