# db/write/poheader_manual_insert.py
import uuid
from db.db_connection import get_connection

# API field -> DB column mapping
COLUMN_MAP = {
    "po_number": "PONumber",
    "po_date": "PODate",
    "hospital_id": "HospitalID",
    "hospital_name": "HospitalName",
    "vendor_gstin": "VendorGSTIN",
    "vendor_code": "VendorCode",
    "awd_name": "AWDName",
    "po_approval_date": "POApprovalDate",
    "rc_number": "RCNumber",
    "rc_validity_date": "RCValidityDate",
}


def insert_po_header_manual(payload):
    """
    Insert POHeader from MANUAL (Power Automate) flow.
    Uses snake_case fields and maps them to DB columns.
    """

    po_id = str(uuid.uuid4())

    columns = ["POID", "IngestionID", "FileID"]
    values = [po_id, payload.ingestion_id, payload.file_id]
    placeholders = ["?", "?", "?"]

    # Convert payload to dict safely
    data = payload.model_dump(exclude_unset=True)

    for api_field, db_column in COLUMN_MAP.items():
        value = data.get(api_field)
        if value is not None:
            columns.append(db_column)
            values.append(value)
            placeholders.append("?")

    sql = f"""
        INSERT INTO dbo.POHeader
        ({", ".join(columns)})
        VALUES ({", ".join(placeholders)})
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

    print(f" Manual POHeader inserted → POID: {po_id}")
    return po_id
