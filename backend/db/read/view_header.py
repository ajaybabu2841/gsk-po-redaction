""" 
POID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        IngestionID UNIQUEIDENTIFIER NULL,
        FileID UNIQUEIDENTIFIER NULL,
        PONumber NVARCHAR(200) NULL,
        HospitalID UNIQUEIDENTIFIER NULL,
        PODate DATE NULL,
        AWDName NVARCHAR(255) NULL,
        VendorGSTIN NVARCHAR(50) NULL,
        VendorCode NVARCHAR(100) NULL,
        POApprovalDate DATE NULL,
        RCNumber NVARCHAR(200) NULL,
        RCValidityDate DATE NULL,"""

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

def view_header():
    conn = get_connection()
    cursor = conn.cursor()

    # Query POHeader table
    query = """
    SELECT 
        POID,
        IngestionID,
        FileID,
        PONumber,
        HospitalID,
        PODate,
        AWDName,
        VendorGSTIN,
        VendorCode,
        POApprovalDate,
        RCNumber,
        RCValidityDate
    FROM dbo.POHeader
    ORDER BY POID DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # if not rows:
    #     print("ℹ No headers found in the POHeader table.")
    # else:
    # Convert rows to formatted table
    table = [
        (
            str(row.POID),
            str(row.IngestionID) if row.IngestionID else "-",
            str(row.FileID) if row.FileID else "-",
            row.PONumber or "-",
            str(row.HospitalID),
            str(row.PODate) or "-",
            row.AWDName or "-",
            row.VendorGSTIN or "-",
            row.VendorCode or "-",
            str(row.POApprovalDate) or "-",
            row.RCNumber or "-",
            str(row.RCValidityDate) or "-"
        )
        for row in rows
    ]
    headers = [
        "POID", "IngestionID", "FileID", "PONumber", "HospitalID", 
        "PODate", "AWDName", "VendorGSTIN", "VendorCode", 
        "POApprovalDate", "RCNumber", "RCValidityDate"
    ]

    print("\nPOHeader Table Data:")
    print(tabulate(table, headers, tablefmt="grid"))


    conn.close()

  

if __name__ == "__main__":
    view_header()