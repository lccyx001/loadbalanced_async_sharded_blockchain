import csv
import pymysql
import time
from evalating import counting
from hash_sharding import hash_sharding
from graph_sharding import data_pre_handler,_calculate_sharding,_apply_sharding_result,graph_sharding

def _get_connections():
    conn = pymysql.connect(host="host.docker.internal",port=3307,user="root",password="root",db="blockchain-test", connect_timeout=7200)
    return conn

def load_data_to_mysql(filename):
    def _write_to_mysql():
        sql = "INSERT INTO transactions (`transactionHash`, `from`, `to`, `value`) VALUES (%s, %s, %s, %s)"  
        cursor = conn.cursor()
        cursor.executemany(sql,datas)
        conn.commit()
        print("loading to %d" %idx)

    conn = _get_connections()
    
    with open(filename,) as csvfile:
        reader = csv.reader(csvfile)
        datas = []
        for idx,row in enumerate(reader) :
            if idx==0:
                continue

            if len(datas)==1000:
                _write_to_mysql()
                datas = []

            hash = row[2]
            from_hash = row[3] # 这里可能有 'None' 进去
            to_hash = row[4]
            value = row[8]
            datas.append((hash,from_hash,to_hash,value,))
        else:
            if len(datas)>0:
                _write_to_mysql()

def do_hash_sharding(shard=4,totals=100000):
    a = time.time()
    conn = _get_connections()
    cursor = conn.cursor()
    hash_sharding(cursor,conn,shard,totals=totals)
    b = time.time()
    print("Finish! costs",b-a)
    # counting(cursor, conn, "hash_sharding")

def do_graph_sharding(shard=4,totals=100000):
    a = time.time()
    conn = _get_connections()
    cursor = conn.cursor()
    graph_sharding(cursor,conn,shard,totals)
    b = time.time()
    print("Finish! costs",b-a)
    # counting(cursor, conn, "graph_sharding")

def clear(hash_s=True,graph_s=True):
    cursor = _get_connections().cursor()
    if hash_s:
        cursor.execute("TRUNCATE table hash_sharding;")
    if graph_s:
        cursor.execute("TRUNCATE table graph_sharding;")
        cursor.execute("TRUNCATE table graph_tx;")
        cursor.execute("TRUNCATE table graph_tx_distinct;")
        cursor.execute("TRUNCATE table graph_user_hash;")

    
if __name__ == "__main__":
    # csvdatas = ["../resource/0to999999_BlockTransaction.csv"]
    # for filename in csvdatas:
    #     load_data_to_mysql(filename)

    clear()

    shard = 4 # 分片数
    totals = 100000 # 交易总量
    do_hash_sharding(shard,totals)
    do_graph_sharding(shard,totals)
    
    conn = _get_connections()
    cursor = conn.cursor()
    counting(cursor, conn, "hash_sharding",shard)
    counting(cursor, conn, "graph_sharding",shard)
    