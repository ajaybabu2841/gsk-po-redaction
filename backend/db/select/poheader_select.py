# db/select/poheader_select.py
import pyodbc
import os

from db.db_connection import get_connection

def get_po_id_by_ingestion_file(ingestion_id: str, file_id: str) -> str | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT POID
        FROM dbo.POHeader
        WHERE IngestionID = ? AND FileID = ?
    """, ingestion_id, file_id)

    row = cursor.fetchone()
    conn.close()

    return str(row[0]) if row else None
