import oracledb

def get_connection():
    dsn = oracledb.makedsn("localhost", 1521, service_name="XEPDB1")
    conn = oracledb.connect(user="library_user", password="Library123", dsn=dsn)
    return conn