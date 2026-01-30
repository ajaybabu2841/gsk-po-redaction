# db/write/poheader_insert.py
from db.db_connection import get_connection

def insert_po_header(*,po_number, file_id, header_data=None, ingestion_id=None, hospital_id=None):
    """
    Insert extracted PO header details into dbo.POHeader.
    Returns POID (GUID).

    """
    if header_data and hasattr(header_data, "model_dump"):
        header_data = header_data.model_dump()

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
        INSERT INTO dbo.POHeader 
        (IngestionID, FileID, PONumber, HospitalID, PODate, AWDName, VendorGSTIN, VendorCode,
         POApprovalDate, RCNumber, RCValidityDate,HospitalName)
        OUTPUT inserted.POID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ingestion_id,
        file_id,
        po_number,
        hospital_id,
        header_data.get("PODate") if header_data else None,
        header_data.get("AWDName") if header_data else None,
        header_data.get("VendorGSTIN") if header_data else None,
        header_data.get("VendorCode") if header_data else None,
        header_data.get("POApprovalDate") if header_data else None,
        header_data.get("RCNumber") if header_data else None,
        header_data.get("RCValidityDate") if header_data else None,
        header_data.get("HospitalName") if header_data else None
    ))

    po_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    print(f" POHeader inserted → POID: {po_id}")
    return po_id
