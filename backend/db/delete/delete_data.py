import os
import pyodbc
from dotenv import load_dotenv
# from db_insert_operations import get_connection
from db.db_connection import get_connection


load_dotenv()

# ============================================================
#  DB CONNECTION
# ============================================================
# def get_connection():
#     conn_str = os.getenv("AZURE_SQL_CONN")
#     if not conn_str:
#         raise ValueError("❌ AZURE_SQL_CONN not set in .env")
#     return pyodbc.connect(conn_str, autocommit=True)


# ============================================================
#  MASTER DELETE: Delete ALL DATA
# ============================================================
def delete_all_data(delete_products=False):
    """
    Deletes ALL rows from all tables in foreign-key safe order.
    Does NOT drop schema. Only removes data.

    delete_products = True   → also clears Product table
                      False  → product master is preserved
    """

    print("\nWARNING: You are about to delete ALL data from the database.")
    confirm = input("Type 'DELETE' to confirm: ")

    if confirm.strip().upper() != "DELETE":
        print(" Cancelled.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    print("\n Deleting ALL data in correct FK order...\n")

    delete_order = [
        "POItem",
        "Invoice",
        "MaskedFile",
        "POHeader",
        "FileUpload",
        "Ingestion",
        "Hospital"
    ]

    # Product delete is optional
    if delete_products:
        delete_order.append("Product")

    for table in delete_order:
        cursor.execute(f"DELETE FROM dbo.{table}")
        print(f" Cleared → {table}")

    print("\n All data deleted successfully!\n")


# ============================================================
#  DELETE BY FileID
# ============================================================
def delete_by_file_id(file_id):
    """
    Deletes a single FILE + ALL related records:
    - MaskedFile
    - POItem
    - Invoice
    - POHeader
    - FileUpload
    """
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\nDeleting records linked to FileID = {file_id}\n")

    # Delete related Masked Files
    cursor.execute("DELETE FROM dbo.MaskedFile WHERE FileID = ?", file_id)
    print("Deleted → MaskedFile")

    # Get POIDs attached to this FileID
    cursor.execute("SELECT POID FROM dbo.POHeader WHERE FileID = ?", file_id)
    po_ids = [row[0] for row in cursor.fetchall()]

    # Delete all POItem for each PO
    for po_id in po_ids:
        cursor.execute("DELETE FROM dbo.POItem WHERE POID = ?", po_id)
        print(f" Deleted → POItem for POID={po_id}")

        cursor.execute("DELETE FROM dbo.Invoice WHERE POID = ?", po_id)
        print(f" Deleted → Invoice for POID={po_id}")

    # Delete POHeader
    cursor.execute("DELETE FROM dbo.POHeader WHERE FileID = ?", file_id)
    print(" Deleted → POHeader")

    # Finally delete FileUpload
    cursor.execute("DELETE FROM dbo.FileUpload WHERE FileID = ?", file_id)
    print(" Deleted → FileUpload")

    print("\n All records linked to FileID deleted!\n")


# ============================================================
#  DELETE BY POID
# ============================================================
def delete_by_po_id(po_id):
    """
    Deletes 1 Purchase Order + POItems + Invoices.
    """

    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n Deleting PO and linked items → POID = {po_id}\n")

    cursor.execute("DELETE FROM dbo.POItem WHERE POID = ?", po_id)
    print("Deleted → POItem")

    cursor.execute("DELETE FROM dbo.Invoice WHERE POID = ?", po_id)
    print(" Deleted → Invoice")

    cursor.execute("DELETE FROM dbo.POHeader WHERE POID = ?", po_id)
    print(" Deleted → POHeader")

    print("\n PO deletion completed!\n")


# ============================================================
#  DELETE BY IngestionID
# ============================================================
def delete_by_ingestion_id(ingestion_id):
    """
    Deletes everything under one Ingestion:
    - MaskedFile
    - FileUpload
    - POHeader
    - POItem
    - Invoice
    - Ingestion
    """

    conn = get_connection()
    cursor = conn.cursor()

    print(f"\nDeleting all data for IngestionID = {ingestion_id}\n")

    # First fetch all FileIDs for this ingestion
    cursor.execute("SELECT FileID FROM dbo.FileUpload WHERE IngestionID = ?", ingestion_id)
    file_ids = [row[0] for row in cursor.fetchall()]

    for file_id in file_ids:
        delete_by_file_id(file_id)

    # Delete the ingestion record after its children are deleted
    cursor.execute("DELETE FROM dbo.Ingestion WHERE IngestionID = ?", ingestion_id)
    print(" Deleted → Ingestion")

    print("\n Completed deletion for the specified IngestionID!\n")


# ============================================================
#  CLI MENU (OPTIONAL)
# ============================================================
if __name__ == "__main__":
    print("\n===== DB DELETE TOOL =====")
    print("1. Delete ALL DATA")
    print("2. Delete by FileID")
    print("3. Delete by POID")
    print("4. Delete by IngestionID")

    choice = input("\nSelect option: ")

    if choice == "1":
        delete_all_data()
    elif choice == "2":
        delete_by_file_id(input("Enter FileID: ").strip())
    elif choice == "3":
        delete_by_po_id(input("Enter POID: ").strip())
    elif choice == "4":
        delete_by_ingestion_id(input("Enter IngestionID: ").strip())
    else:
        print(" Invalid choice.")
