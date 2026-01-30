import pyodbc
import os
from db.db_connection import get_connection
# --------------------------------------------------
# API field → DB column mapping
# --------------------------------------------------
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


def update_po_header(po_id: str, fields: dict):
    """
    Updates only the provided fields in dbo.POHeader.
    Fields are mapped safely from API names to DB column names.
    """

    # Fields that should NEVER be updated
    ignore = {"po_id", "ingestion_id", "file_id"}
    fields = {k: v for k, v in fields.items() if k not in ignore}

    if not fields:
        return  # nothing to update

    set_parts = []
    values = []

    for api_field, value in fields.items():
        db_column = COLUMN_MAP.get(api_field)
        if not db_column:
            continue  # skip unknown / unsupported fields

        set_parts.append(f"{db_column} = ?")
        values.append(value)

    if not set_parts:
        return  # no valid columns to update

    set_clause = ", ".join(set_parts)

    sql = f"""
        UPDATE dbo.POHeader
        SET {set_clause}
        WHERE POID = ?
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, values + [po_id])
    conn.commit()
    conn.close()
