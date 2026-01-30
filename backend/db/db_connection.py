import os
import time
import pyodbc
pyodbc.pooling = True
from dotenv import load_dotenv

load_dotenv()


def get_connection(max_retries=5, delay=5, first_try_delay=5):
    """
    Establish connection to Azure SQL with enhanced retry handling.
    """
    conn_str = os.getenv("AZURE_SQL_CONN")
    if not conn_str:
        raise ValueError(" AZURE_SQL_CONN environment variable not set.")
    
    print(" Waiting a few seconds before first connection attempt...")
    time.sleep(first_try_delay)
    
    last_error = None  # Store the last error to raise if all attempts fail
    
    for attempt in range(max_retries):
        try:
            print(f" Attempting connection (try {attempt+1}/{max_retries})...")
            
            # Remove timeout parameter - it's already in connection string
            conn = pyodbc.connect(conn_str, autocommit=True)
            
            # Test the connection with a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            print(" Connection established successfully.")
            return conn
            
        except (pyodbc.InterfaceError, pyodbc.OperationalError, pyodbc.Error) as e:
            print(f" Connection Error: {e}")
            last_error = e
        
        if attempt < max_retries - 1:
            print(f" Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print(" All connection attempts failed.")
    if last_error:
        raise last_error
    else:
        raise Exception("Connection failed after all retries")
 