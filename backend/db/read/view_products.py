import os
import pyodbc
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

def get_connection():
    conn_str = os.getenv('AZURE_SQL_CONN')
    if not conn_str:
        raise ValueError('❌ AZURE_SQL_CONN not set in .env file')
    return pyodbc.connect(conn_str)

def view_products():
    """Fetch and display all products from the dbo.Product table."""
    conn = get_connection()
    cursor = conn.cursor()

    # Query Product table
    query = """
    SELECT 
        ProductID,
        ProductName,
        GMMCode,
        HSNCode,
        MRP,
        DateCreated,
        DateModified,
        ValidTill
    FROM dbo.Product
    ORDER BY DateCreated DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        print("ℹNo products found in the Product table.")
    else:
        # Convert rows to formatted table
        table = [
            (
                str(row.ProductID),
                row.ProductName,
                row.GMMCode or "-",
                row.HSNCode or "-",
                row.MRP if row.MRP is not None else "-",
                row.DateCreated.strftime("%Y-%m-%d %H:%M:%S") if row.DateCreated else "-",
                row.DateModified.strftime("%Y-%m-%d %H:%M:%S") if row.DateModified else "-",
                row.ValidTill.strftime("%Y-%m-%d") if row.ValidTill else "-"
            )
            for row in rows
        ]

        print("\n Product Table Data:")
        print(tabulate(
            table,
            headers=["ProductID", "ProductName", "GMMCode", "HSNCode", "MRP", "DateCreated", "DateModified", "ValidTill"],
            tablefmt="grid"
        ))

    conn.close()

if __name__ == "__main__":
    view_products()
