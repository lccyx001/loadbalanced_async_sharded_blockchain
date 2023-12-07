import csv
import pymysql
import time
from hash_sharding import make_sharding
from graph_sharding import data_pre_handler,calculate_sharding,apply_sharding_result

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

def do_hash_sharding(shard=4):
    offset = 0
    limit = 1000
    conn = _get_connections()
    cursor = conn.cursor()
    while True:
        start = time.time()
        query_sql = "SELECT `transactionHash`, `from`, `to`, `value` FROM transactions LIMIT {offset}, {limit};"
        cursor.execute(query_sql.format(offset=offset,limit=limit))
        res = cursor.fetchall()
        if not len(res):
            break
        datas = make_sharding(res, 4)
        # print(datas[0])
        def _write_to_mysql():
            sql = "INSERT INTO hash_sharding (`transactionHash`, `from`, `to`, `value`,`from_shard`,`to_shard`,`cross`) VALUES (%s, %s, %s, %s, %s, %s, %s)"  
            cursor.executemany(sql,datas)
            conn.commit()
            end = time.time()
            print("loading to %d, costs %d seconds." % (offset,end-start) )
            

        _write_to_mysql()
        offset += limit

def counting(tablename="hash_sharding"):
    conn = _get_connections()
    cursor = conn.cursor()
    query_sql = "select count(1) from {}".format(tablename)
    cursor.execute(query_sql)
    total =cursor.fetchall()[0][0]
    
    cursor.execute("select count(1) from {} WHERE `cross` = 1;".format(tablename))
    cross = cursor.fetchall()[0][0]

    print("total txs: %d cross txs: %d, cross percentage %f" % (total, cross, cross/total))

def do_graph_sharding(shard=4):
    conn = _get_connections()
    cursor = conn.cursor()
    data_pre_handler(cursor,conn)
    calculate_sharding(cursor,conn,shard)
    apply_sharding_result(cursor,conn)
    # 直接一个batch一个batch的执行
    


        
if __name__ == "__main__":
    # csvdatas = ["../resource/0to999999_BlockTransaction.csv"]
    # for filename in csvdatas:
    #     load_data_to_mysql(filename)
    # do_hash_sharding()
    counting("graph_sharding")
    counting("hash_sharding")
    # do_graph_sharding()