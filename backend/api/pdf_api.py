import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Union
 
from models.po_models import ProcessPDFResponse, BlobProcessRequest, ManualRedactionResponse
from process_po import process_pdf
from utils.logging.logger import get_logger
from utils.azure.blob_reader import download_blob_as_bytes
from models.po_models import HospitalCreate, HospitalUpdate, ProductInsert
from db.insert.hospital_insert import insert_hospital
from db.update.hospital_update import update_hospital_by_rcno
logger = get_logger(__name__)
router = APIRouter(prefix="/pdf", tags=["PDF"])
 
 
# @router.post("/upload", response_model=Union[ProcessPDFResponse, ManualRedactionResponse])
# async def upload_pdf(file: UploadFile = File(...)):
#     logger.info("PDF upload request received", extra={"filename": file.filename})
 
#     if not file.filename.lower().endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
 
#     try:
#         pdf_bytes = await file.read()
#         return process_pdf(pdf_bytes, file.filename)
 
#     except Exception:
#         logger.exception("PDF processing failed", extra={"filename": file.filename})
#         raise HTTPException(status_code=500, detail="Internal error while processing PDF")
 
 
# @router.get("/view")
# async def view_pdf(path: str = Query(...)):
#     if not path.startswith("temp"):
#         raise HTTPException(status_code=400, detail="Invalid file path.")
 
#     if not os.path.exists(path):
#         raise HTTPException(status_code=404, detail="File not found.")
 
#     return FileResponse(path, media_type="application/pdf")
 
 
# @router.post("/process-blob")
# async def process_blob_pdf(req: BlobProcessRequest):
#     logger.info("Blob processing trigger received", extra=req.model_dump())
 
#     try:
#         pdf_stream = download_blob_as_bytes(
#             storage_account=req.storage_account,
#             container_name=req.container_name,
#             blob_file_name=req.blob_file_name
#         )
 
#         pdf_bytes = pdf_stream.getvalue()
#         process_pdf(pdf_bytes, req.blob_file_name)
 
#         return {"status": "received"}
 
#     except Exception:
#         logger.exception("Blob processing trigger failed")
#         raise HTTPException(status_code=500, detail="Blob processing failed")

@router.post("/process-blob")
async def process_blob_pdf(req: BlobProcessRequest):
 
    storage_account = req.storage_account
    container_name = req.container_name
    blob_file_name = req.blob_file_name
    file_id = req.file_id
    ingestion_id = req.ingestion_id
 
    logger.info(
        "Blob processing trigger received",
        extra={
            "storage_account": storage_account,
            "container_name": container_name,
            "blob_file_name": blob_file_name,
            "file_id": file_id,
            "ingestion_id": ingestion_id
        }
    )
 
    if not file_id or not ingestion_id:
        logger.error(
            "Missing mandatory identifiers from Power Automate",
            extra={
                "file_id": file_id,
                "ingestion_id": ingestion_id
            }
        )
        raise HTTPException(
            status_code=400,
            detail="file_id and ingestion_id are mandatory for blob processing"
        )
 
    try:
        # ---- your processing logic will go here later ----
        # For now, just confirm receipt
        pdf_stream = download_blob_as_bytes(
            storage_account=req.storage_account,
            container_name=req.container_name,
            blob_file_name=req.blob_file_name
        )
 
        pdf_bytes = pdf_stream.getvalue()
 
        result = process_pdf(
            pdf_bytes=pdf_bytes,
            file_name=blob_file_name,
            file_id=file_id,
            ingestion_id=ingestion_id
        )
 
        logger.info(
            "Blob processing completed successfully",
            extra={
                "file_id": file_id,
                "ingestion_id": ingestion_id
            }
        )
 
        return {
            "storage_account": storage_account,
            "container_name": container_name,
            "blob_file_name": blob_file_name,
            "file_id": file_id,
            "ingestion_id": ingestion_id
        }
 
    except Exception as e:
        logger.exception(
            "Blob processing trigger failed",
            extra={
                "blob_file_name": blob_file_name,
                "ingestion_id": ingestion_id
            }
        )
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/hospitals", status_code=201)
def create_hospital(payload: HospitalCreate):
    hospital_id = insert_hospital(payload)
    return {
        "status": "created",
        "HospitalID": str(hospital_id)
    }


@router.patch("/hospitals/by-rcno/{rc_no}")
def update_hospital_by_rc(
    rc_no: int,
    payload: HospitalUpdate
):
    # At least one field required
    if payload.HospitalEmail is None and payload.RCExtension is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of HospitalEmail or RCExtension must be provided"
        )

    try:
        updated_fields = update_hospital_by_rcno(
            rc_no=rc_no,
            payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not updated_fields:
        return {
            "status": "no_change",
            "RCNo": rc_no
        }

    return {
        "status": "updated",
        "RCNo": rc_no,
        "updatedFields": updated_fields
    }

# @router.post("/productsinsert/by-injestion-id and po-id/{ingestion_id}/{po_id}")
# def insert_products_by_ingestion_and_po(ingestion_id: str, po_id: str, payload: ProductInsert):
#     product_id = insert_product(payload)
#     return {
#         "status": "created",
#         "ProductID": str(product_id)
#     }

