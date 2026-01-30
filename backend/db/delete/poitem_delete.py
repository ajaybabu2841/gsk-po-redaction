from db.db_connection import get_connection

def delete_po_items_by_poid(po_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM dbo.POItem WHERE POID = ?",
        [po_id]
    )
    rows_deleted = cursor.rowcount
    print(f"Rows deleted for POID {po_id}: {rows_deleted}")
    
    conn.commit()
    conn.close()
    print(f" POItems deleted for POID: {po_id}")