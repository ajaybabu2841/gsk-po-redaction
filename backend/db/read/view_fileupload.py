"""
FileID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        IngestionID UNIQUEIDENTIFIER NULL,
        FileName NVARCHAR(500) NOT NULL,
        BlobURL NVARCHAR(MAX) NULL,
        ReceivedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
        KYCVerified BIT NULL,
"""

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

########################### File Upload Read Operation #############################

def view_fileupload():
    conn = get_connection()
    cursor = conn.cursor()

    # Query FileUpload table
    query = """
    SELECT 
        FileID,
        IngestionID,
        FileName,
        BlobURL,
        ReceivedAt,
        KYCVerified
    FROM dbo.FileUpload
    ORDER BY FileID DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # if not rows:
    #     print("ℹ No files found in the FileUpload table.")
    # else:
    # Convert rows to formatted table
    table = [
        (
            str(row.FileID),
            str(row.IngestionID),
            row.FileName,
            row.BlobURL,
            row.ReceivedAt.strftime("%Y-%m-%d %H:%M:%S"),
            str(row.KYCVerified)
        )
        for row in rows
    ]

    headers = ["FileID", "IngestionID", "FileName", "BlobURL", "ReceivedAt", "KYCVerified"]
    print("\n FileUpload Table Data:")
    print(tabulate(table, headers, tablefmt="grid"))

    conn.close()

if __name__ == "__main__":
    view_fileupload()

