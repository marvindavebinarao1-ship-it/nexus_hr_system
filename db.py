import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='hr_management',
            user='root',
            password=''  # Default XAMPP MySQL password is blank
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None