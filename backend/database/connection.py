from dotenv import load_dotenv
import os
import cx_Oracle
from urllib.parse import urlparse

load_dotenv()  # Load environment variables from .env file

jdbc_url = os.getenv("ORACLE_JDBC_URL")
username = os.getenv("ORACLE_USER")
password = os.getenv("ORACLE_PASSWORD")
port = os.getenv("PORT")
service_name = os.getenv("SERVICE")

#print(jdbc_url, username, password)

dsn = cx_Oracle.makedsn(jdbc_url, port, service_name=service_name)

#print(dsn)
try:
    # Connect to the database
    connection = cx_Oracle.connect(username, password, dsn)
    print("Connection successful!")

    # Create a cursor
    cursor = connection.cursor()

    # Run a sample query, replace 'your_table' with a real table name
    cursor.execute("SELECT * FROM ASRIT_PATIENT WHERE ROWNUM = 1")
    result = cursor.fetchone()
    print("Sample query result:", result)

except cx_Oracle.DatabaseError as e:
    print("Database connection or query failed:", e)

finally:
    if 'connection' in locals():
        connection.close()
