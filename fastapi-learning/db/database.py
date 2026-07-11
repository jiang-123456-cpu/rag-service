import pymysql
import pymysql.cursors


def get_db():
    """每次调用创建一个新的数据库连接和游标"""
    conn = pymysql.connect(
        host="localhost",
        user="root",         # 你的MySQL账号
        password="123456",   # 你的密码
        database="backend",   # 库名
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor  # 使用字典游标，返回字典而不是元组
    )
    return conn
# def execute_sql(sql: str, params: tuple = ()):
#     """执行写操作（INSERT, UPDATE, DELETE）并返回影响行数及自增ID"""
#     # conn = get_db_connection()
#     # cursor = conn.cursor()
#     try:
#         cursor.execute(sql, params)
#         conn.commit()
#         last_id = cursor.lastrowid
#         affected = cursor.rowcount
#         return {"affected": affected, "last_id": last_id}
#     except pymysql.Error as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     finally:
#         cursor.close()
#         conn.close()