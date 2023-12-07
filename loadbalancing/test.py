# import pymysql

# # Assuming you already have a connection to your MySQL database
# connection = pymysql.connect(host="host.docker.internal",port=3307,user="root",password="root",db="blockchain-test", connect_timeout=7200)

# try:
#     with connection.cursor() as cursor:
#         # SQL update statement
#         # update_query = "update graph_user_hash set `shard`=%s where id=%s"

#         # # Data for batch update
#         # update_data = [
#         #     (1,1),
#         #     (1,2),
#         #     # Add more tuples as needed
#         # ]

#         # # Execute the batch update
#         # cursor.executemany(update_query, update_data)
#         cursor.execute("select min(id) from graph_user_hash;")
#         minid = cursor.fetchone()[0]
#         print(minid)

#     # Commit the changes
#     connection.commit()

# finally:
#     # Close the connection
#     connection.close()
if not True or not False:
    print(1)