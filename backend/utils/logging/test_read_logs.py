# # test_read_logs_pretty.py
# import pyodbc
# import os
# from dotenv import load_dotenv
# from tabulate import tabulate

# load_dotenv()

# conn = pyodbc.connect(os.getenv("AZURE_SQL_CONN"))
# cursor = conn.cursor()

# cursor.execute("""
# SELECT TOP 20 *
# FROM AppLogs
# ORDER BY CreatedAt DESC
# """)

# rows = cursor.fetchall()
# columns = [column[0] for column in cursor.description]

# print(tabulate(rows, headers=columns, tablefmt="psql"))

# test_read_logs_pretty.py
import pyodbc
import os
from dotenv import load_dotenv
from tabulate import tabulate
import json

load_dotenv()

conn = pyodbc.connect(os.getenv("AZURE_SQL_CONN"))
cursor = conn.cursor()

cursor.execute("""
SELECT TOP 30 *
FROM AppLogs
ORDER BY CreatedAt DESC
""")

rows = cursor.fetchall()
columns = [column[0] for column in cursor.description]

clean_rows = []

for r in rows:
    r = list(r)

    # RawLog is usually the last column
    raw_log = r[-1]

    if raw_log:
        raw_log_str = str(raw_log)
        if len(raw_log_str) > 120:
            raw_log_str = raw_log_str[:120] + " ... (truncated)"
        r[-1] = raw_log_str

    clean_rows.append(r)

print(tabulate(clean_rows, headers=columns, tablefmt="psql"))
