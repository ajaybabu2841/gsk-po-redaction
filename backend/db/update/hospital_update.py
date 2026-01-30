from datetime import datetime
from zoneinfo import ZoneInfo
from db.db_connection import get_connection
from utils.logging.logger import get_logger

logger = get_logger(__name__)
IST = ZoneInfo("Asia/Kolkata")


def update_hospital_by_rcno(*, rc_no: int, payload):
    """
    Update ONLY HospitalEmail and/or RCExtension using RCNo as identifier.
    Returns list of updated fields.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # 1️⃣ Fetch existing values
    cursor.execute(
        """
        SELECT HospitalID, HospitalEmail, RCExtension
        FROM dbo.Hospital
        WHERE RCNo = ?
        """,
        (rc_no,)
    )

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Hospital not found for given RCNo")

    hospital_id, existing_email, existing_rc_ext = row

    updates = {}
    updated_fields = []

    # 2️⃣ Detect changes
    if payload.HospitalEmail is not None and payload.HospitalEmail != existing_email:
        updates["HospitalEmail"] = payload.HospitalEmail
        updated_fields.append("HospitalEmail")

    if payload.RCExtension is not None and payload.RCExtension != existing_rc_ext:
        updates["RCExtension"] = payload.RCExtension
        updated_fields.append("RCExtension")

    if not updates:
        conn.close()
        return []

    # updates["UpdatedAt"] = datetime.now(IST)
    updates["RCNo"] = rc_no

    # 3️⃣ Dynamic UPDATE (pyodbc-compatible)

    set_clause = ", ".join(f"{k} = ?" for k in updates if k != "RCNo")

    values = [
        updates[k] for k in updates if k != "RCNo"
    ]
    values.append(rc_no)  # for WHERE RCNo = ?

    cursor.execute(
        f"""
        UPDATE dbo.Hospital
        SET {set_clause}
        WHERE RCNo = ?
        """,
        values
    )


    conn.commit()
    conn.close()

    logger.info(
        "Hospital updated using RCNo",
        extra={
            "HospitalID": str(hospital_id),
            "RCNo": rc_no,
            "updated_fields": updated_fields
        }
    )

    return updated_fields
 