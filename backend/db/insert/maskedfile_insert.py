from db.db_connection import get_connection

def insert_masked_file(file_id, masked_blob_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dbo.MaskedFile
            (FileID, MaskedFileName, MaskedFileURL, ProcessedAt)
            OUTPUT inserted.MaskedFileID
            VALUES (?, ?, ?, SYSUTCDATETIME())

    """, (
        file_id,
        masked_blob_name,
        masked_blob_name  # using blob name as URL
    ))

    masked_file_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    print(f" MaskedFile inserted → MaskedFileID: {masked_file_id}")
    return masked_file_id
