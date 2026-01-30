import os
import pyodbc
from dotenv import load_dotenv
from backend.db.seed.sheet_data import GSK_PRODUCTS_LIST
# from db_insert_operations import get_connection
from db.db_connection import get_connection


# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")


def insert_products(products):
    inserted, skipped = 0, 0
    with get_connection() as conn:
        cursor = conn.cursor()
        for product_name in products:
            # Check if product already exists
            cursor.execute("SELECT COUNT(*) FROM dbo.Product WHERE ProductName = ?", (product_name,))
            exists = cursor.fetchone()[0] > 0

            if not exists:
                cursor.execute("INSERT INTO dbo.Product (ProductName) VALUES (?)", (product_name,))
                inserted += 1
                print(f" Inserted: {product_name}")
            else:
                skipped += 1
                print(f" Skipped (already exists): {product_name}")

        conn.commit()
    print(f"\n Summary → Inserted: {inserted} | Skipped: {skipped}")

if __name__ == "__main__":
    insert_products(GSK_PRODUCTS_LIST)
