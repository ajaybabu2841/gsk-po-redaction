"""MaskedFileID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        FileID UNIQUEIDENTIFIER NOT NULL,
        MaskedFileName NVARCHAR(500) NULL,
        MaskedFileURL NVARCHAR(MAX) NULL,
        AccuracyPercent DECIMAL(5,2) NULL,
        ProcessedAt DATETIME2(3) NULL,"""


import os
import pyodbc
from dotenv import load_dotenv
from tabulate import tabulate
load_dotenv()

def get_connection():
    """Get database connection from environment variable."""
    conn_str = os.getenv('AZURE_SQL_CONN')
    if not conn_str:
        raise ValueError('AZURE_SQL_CONN environment variable not set')
    return pyodbc.connect(conn_str)

def view_masked_items():
    conn = get_connection()
    cursor = conn.cursor()

    # Query MaskedFile table
    query = """
    SELECT 
        MaskedFileID,
        FileID,
        MaskedFileName,
        MaskedFileURL,
        AccuracyPercent,
        ProcessedAt
    FROM dbo.MaskedFile
    ORDER BY MaskedFileID DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # if not rows:
    #     print("ℹ No masked items found in the MaskedFile table.")
    # else:
    # Convert rows to formatted table
    table = [
        (
            str(row.MaskedFileID),
            str(row.FileID),
            row.MaskedFileName,
            row.MaskedFileURL,
            str(row.AccuracyPercent),
            str(row.ProcessedAt)
        )
        for row in rows
    ]

    headers = [
        "MaskedFileID",
        "FileID",
        "MaskedFileName",
        "MaskedFileURL",
        "AccuracyPercent",
        "ProcessedAt"
    ]

    print("\n MaskedFile Table Data:")
    print(tabulate(table, headers, tablefmt="grid"))
    
    conn.close()

if __name__ == "__main__":
    view_masked_items()

