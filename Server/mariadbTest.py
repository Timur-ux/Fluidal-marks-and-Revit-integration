# import mariadb
# import sys
#
# try:
#     connection = mariadb.connect(
#             user="root",
#             password="qwerty",
#             host="127.0.0.1",
#             port=3306,
#             database="RevitObjectsStore"
#             )
# except mariadb.Error as e:
#     print(f"Error: conneting to mariaDB failed: {e}")
#     sys.exit(1)
#
# cursor = connection.cursor()
#
# cursor.execute("SELECT * FROM objects")
#
# it = iter(cursor)
# print(list(it))
import DataBase
from objectData import ObjectData

db = DataBase.MariaDBAdapter("./Server/MariaDBConfig.json")
print(db.getData(2233).pos())
db.setData(ObjectData("abcd", "parampampam", 1, 1, 1, 2233))
print(db.getData(2233).pos())
