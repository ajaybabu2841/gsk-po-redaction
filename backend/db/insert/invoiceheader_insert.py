# db/insert/invoiceheader_insert.py
from db.db_connection import get_connection

def insert_invoice_header(*, po_number, file_id, invoice_number=None, header_data=None, ingestion_id=None, hospital_id=None):
    """
    Insert extracted Invoice header details into dbo.InvoiceHeader.
    Returns InvoiceHeaderID (GUID).
    """
    if header_data and hasattr(header_data, "model_dump"):
        header_data = header_data.model_dump()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dbo.InvoiceHeader 
        (IngestionID, FileID, PONumber, InvoiceNumber, HospitalName, HospitalID, AWDName, AWDCERPSCode, InvoiceDate)
        OUTPUT inserted.InvoiceHeaderID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ingestion_id,
        file_id,
        po_number,
        invoice_number,
        header_data.get("HospitalName") if header_data else None,
        hospital_id,
        header_data.get("AWDName") if header_data else None,
        header_data.get("AWDCERPSCode") if header_data else None,
        header_data.get("InvoiceDate") if header_data else None
    ))

    invoice_header_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    print(f" InvoiceHeader inserted → InvoiceHeaderID: {invoice_header_id}")
    return invoice_header_id
