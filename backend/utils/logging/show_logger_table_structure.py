import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")

if not AZURE_SQL_CONN:
    raise ValueError("❌ AZURE_SQL_CONN not found in .env file")

QUERY = """
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'AppLogs'
ORDER BY ORDINAL_POSITION;
"""

def show_table_structure():
    print(" Connecting to Azure SQL Database...")
    with pyodbc.connect(AZURE_SQL_CONN) as conn:
        cursor = conn.cursor()
        print("Connected successfully\n")

        print(" Table Structure for dbo.AppLogs:\n")

        cursor.execute(QUERY)
        rows = cursor.fetchall()

        for row in rows:
            print(f" Column: {row.COLUMN_NAME}")
            print(f"   ├─ Type: {row.DATA_TYPE} ({row.CHARACTER_MAXIMUM_LENGTH})")
            print(f"   └─ Nullable: {row.IS_NULLABLE}")
            print()

if __name__ == "__main__":
    show_table_structure()