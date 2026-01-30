import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

conn = pyodbc.connect(os.getenv("AZURE_SQL_CONN"))
cursor = conn.cursor()

cursor.execute("SELECT TOP 50 * FROM ErrorDump ORDER BY CreatedAt DESC")

rows = cursor.fetchall()

for r in rows:
    print("---- ERROR ROW ----")
    print("ErrorID:", r.ErrorID)
    print("RequestID:", r.RequestID)
    print("FileName:", r.FileName)
    print("Stage:", r.Stage)
    print("ErrorCategory:", r.ErrorCategory)
    print("ErrorMessage:", r.ErrorMessage[:200], "...")
    print("CreatedAt:", r.CreatedAt)
    print()
