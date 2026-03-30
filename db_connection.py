import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "192.168.100.55",
    "user": "root",
    "password": "P@ssw0rd",
    "database": "pet_hotel",  # 🔥 เปลี่ยนตรงนี้
}


def get_db_connection():
    """Create and return a new database connection to MariaDB."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as err:
        if err.errno == 2003:
            print("Error: Cannot connect to MariaDB server")
        elif err.errno == 1045:
            print("Error: Access denied (check username/password)")
        elif err.errno == 1049:
            print("Error: Unknown database (database not found)")
        else:
            print(f"Error connecting to database: {err}")
        raise
