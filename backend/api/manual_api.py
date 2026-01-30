from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import date

from db.insert.poheader_manual_insert import insert_po_header_manual
from db.insert.poitem_manual_insert import insert_po_items_manual
from db.delete.poitem_delete import delete_po_items_by_poid
from models.po_models import ManualPOHeaderRequest, ManualPOItemRequest
from db.select.poheader_select import get_po_id_by_ingestion_file
from db.update.poheader_update import update_po_header
from utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/manual", tags=["Manual"])

import uuid

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False

@router.post("/po/header")
def manual_po_header(payload: ManualPOHeaderRequest):
    """
    This endpoint is called ONLY by Power Automate.

    Behaviour:
    - If po_id is provided → update that POHeader
    - If po_id is not provided:
        - Try finding POHeader using ingestion_id + file_id
        - If found → update
        - Else → insert new POHeader
    """

    try:
        logger.info(
            "Manual PO header request received",
            extra={
                "ingestion_id": payload.ingestion_id,
                "file_id": payload.file_id,
                "po_id": payload.po_id
            }
        )

        # -----------------------------
        # STEP 1: Resolve POID
        # -----------------------------
        po_id = payload.po_id

        if not po_id:
            po_id = get_po_id_by_ingestion_file(
                ingestion_id=payload.ingestion_id,
                file_id=payload.file_id
            )

        # -----------------------------
        # STEP 2: UPDATE existing PO
        # -----------------------------
        if po_id:
            update_po_header(
                po_id=po_id,
                fields=payload.dict(exclude_unset=True)
            )

            logger.info(
                "Manual PO header updated",
                extra={"po_id": po_id}
            )

            return {
                "status": "success",
                "action": "updated",
                "po_id": po_id
            }

        # -----------------------------
        # STEP 3: INSERT new PO
        # -----------------------------

        if not payload.po_number:
            raise HTTPException(
                status_code=400,
                detail="po_number is required when creating a new PO"
            )



        po_id = insert_po_header_manual(payload)

        logger.info(
            "Manual PO header inserted",
            extra={"po_id": po_id}
        )

        return {
            "status": "success",
            "action": "inserted",
            "po_id": po_id
        }

    except Exception as exc:
        logger.exception(
            "Manual PO header processing failed",
            extra={
                "ingestion_id": payload.ingestion_id,
                "file_id": payload.file_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

# ======================================================


@router.post("/po/items")
def manual_po_items(payload: ManualPOItemRequest):
    try:
        logger.info(
            "Manual PO items request received",
            extra={
                "po_id": payload.po_id,
                "item_count": len(payload.items)
            }
        )

        # 1️⃣ Remove old items
        delete_po_items_by_poid(payload.po_id)

        # 2️⃣ Insert new manual items
        insert_po_items_manual(
            po_id=payload.po_id,
            items=payload.items
        )

        return {
            "status": "success",
            "po_id": payload.po_id,
            "inserted_items": len(payload.items)
        }

    except Exception as exc:
        logger.exception(
            "Manual PO items processing failed",
            extra={"po_id": payload.po_id}
        )
        raise HTTPException(status_code=500, detail=str(exc))