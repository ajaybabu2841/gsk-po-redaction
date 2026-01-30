"""
POItemID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        POID UNIQUEIDENTIFIER NOT NULL,
        ProductID UNIQUEIDENTIFIER NULL,
        UnitOfMeasure NVARCHAR(50) NULL,
        HSNCode NVARCHAR(50) NULL,
        Quantity INT NULL,
        GSKQuantity INT NULL,
        Price DECIMAL(18,6) NULL,
        RCRate DECIMAL(18,6) NULL,
        ItemCodeFromPO NVARCHAR(200) NULL,
        Marked BIT NULL,
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

def view_items():
    conn = get_connection()
    cursor = conn.cursor()

    # Query POItem table
    query = """
    SELECT 
        POItemID,
        POID,
        ProductID,
        UnitOfMeasure,
        HSNCode,
        Quantity,
        GSKQuantity,
        Price,
        RCRate,
        ItemCodeFromPO,
        Marked
    FROM dbo.POItem
    ORDER BY POItemID DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # if not rows:
    #     print("ℹNo items found in the POItem table.")
    # else:
    # Convert rows to formatted table
    table = [
        (
            str(row.POItemID),
            str(row.POID),
            str(row.ProductID) if row.ProductID else "-",
            row.UnitOfMeasure or "-",
            row.HSNCode or "-",
            row.Quantity if row.Quantity is not None else "-",
            row.GSKQuantity if row.GSKQuantity is not None else "-",
            row.Price if row.Price is not None else "-",
            row.RCRate if row.RCRate is not None else "-",
            row.ItemCodeFromPO or "-",
            "Yes" if row.Marked else "No"
        )
        for row in rows
    ]
    print("\nPOItem Table Data:")
    print(tabulate(
        table,
        headers=["POItemID", "POID", "ProductID", "UnitOfMeasure", "HSNCode", "Quantity", "GSKQuantity", "Price", "RCRate", "ItemCodeFromPO", "Marked"],
        tablefmt="grid"
    ))
    conn.close()

if __name__ == "__main__":
    view_items()