# db/write/fileupload_insert.py
from db.db_connection import get_connection

def insert_file_upload(filename, blob_name, ingestion_id=None):
    """
    Stores a PDF upload record in dbo.FileUpload.
    Returns FileID (GUID).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dbo.FileUpload 
        (IngestionID, FileName, BlobURL, ReceivedAt, KYCVerified)
        OUTPUT inserted.FileID
        VALUES (?, ?, ?, SYSUTCDATETIME(), NULL)
    """, (ingestion_id, filename, blob_name))

    file_id = cursor.fetchone()[0]
    conn.close()

    print(f"FileUpload inserted → FileID: {file_id}")
    return file_id