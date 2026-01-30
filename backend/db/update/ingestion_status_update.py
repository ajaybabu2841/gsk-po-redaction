from db.db_connection import get_connection

def update_ingestion_status(ingestion_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE dbo.Ingestion
        SET Status = ?
        WHERE IngestionID = ?
    """, (status, ingestion_id))

    conn.commit()
    conn.close()
    