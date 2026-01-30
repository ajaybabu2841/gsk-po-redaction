
from uuid import uuid4
from zoneinfo import ZoneInfo
from datetime import datetime
from db.db_connection import get_connection


from utils.logging.logger import get_logger

logger = get_logger(__name__)
IST = ZoneInfo("Asia/Kolkata")

def insert_hospital(payload):
    hospital_id = uuid4()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO dbo.Hospital (
            HospitalID,
            HospitalName,
            City,
            State,
            HospitalEmail,
            CreatedAt,
            RCNo,
            RcCreatorName,
            PriceApprovalfrPeriod,
            PriceApprovaltoPeriod,
            AtHo,
            RCExtension
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            hospital_id,
            payload.HospitalName,
            payload.City,
            payload.State,
            payload.HospitalEmail,
            datetime.now(IST),
            payload.RCNo,
            payload.RcCreatorName,
            payload.PriceApprovalfrPeriod,
            payload.PriceApprovaltoPeriod,
            payload.AtHo,
            payload.RCExtension,
        )
    )

    conn.commit()
    conn.close()

    logger.info(
        "Hospital inserted",
        extra={"HospitalID": str(hospital_id)}
    )

    return hospital_id
 