import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="roza@123",
    database="ats_db"
)

print("MySQL connected successfully!")

