# services/process_po.py
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
import requests
import sys

from db.update.ingestion_status_update import update_ingestion_status
from utils.logging.logger import get_logger
from utils.stage0.pdf_to_bytes import load_pdf_as_bytes
from utils.stage0.pdf_bytes_to_image import pdf_bytes_to_images
from utils.stage1_llm_classifier.llm_classifier import classify_po_pdf_from_images
from utils.stage2_llm_extraction_as_it_is.getAllMedicines import extract_all_medicines_from_images
from utils.stage2_llm_extraction_as_it_is.gsk_products_list import GSK_BRANDS
from utils.stage2_llm_extraction_as_it_is.non_gsk_filteration import filter_non_gsk_medicines
from utils.stage3_po_item_extraction.po_itemlist_extract import extract_po_items_from_pdf_pages
from utils.stage4_ocr_grid.stage4_0_ocr import run_adi_ocr
from utils.stage4_ocr_grid.stage4_1_orchestrator import evaluate_tables_for_po
# from utils.stage5_find_row_col_idx.find_coordinates import find_non_gsk_row_spans
from utils.stage5_find_row_col_idx.matcher import find_fragmented_match
from utils.stage5_find_row_col_idx.get_max_width import get_table_x_bounds
from utils.stage5_find_row_col_idx.get_row_y1_y2 import get_y1_y2_from_ocr
from utils.stage5_find_row_col_idx.redaction import redact_pdf_from_stream_with_spans
from utils.stage2_llm_extraction_as_it_is.po_header_extractor import extract_POHeader_data_from_bytes
from utils.azure.upload_bytes import upload_bytes_to_blob
from db.insert.poheader_insert import insert_po_header
from db.insert.maskedfile_insert import insert_masked_file
from db.insert.poitem_insert import insert_po_items
from utils.logging.error_handler import log_processing_failure
from utils.stage2_llm_extraction_as_it_is.layout_result import get_layout_result
from utils.stage2_llm_extraction_as_it_is.get_medicine_list_from_layout import medicine_names_layout
from utils.stage2_llm_extraction_as_it_is.build_layout_index import build_layout_index_for_non_gsk

 

logger = get_logger(__name__)

REDACTED_OUTPUT = "REDACTED_OUTPUT"
POWER_AUTOMATE_WEBHOOK_URL = os.getenv("POWER_AUTOMATE_WEBHOOK_URL")
POWER_AUTOMATE_ERROR_WEBHOOK_URL = os.getenv("POWER_AUTOMATE_ERROR_WEBHOOK_URL")

# pdf_name = sys.argv[1]  # expects: python runner.py file.pdf
# logger.info(f"📄 Starting PO processing pipeline for file: {pdf_name}")

# print(f"Processing: {pdf_name}")

def build_masked_blob_name(file_id: str, original_file_name: str) -> str:
    base_name = os.path.splitext(original_file_name)[0]

    # Sanitize filename (keep it blob-safe)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", base_name)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    return f"{file_id}_{safe_name}_{timestamp}_redacted.pdf"

def normalize_guid(value: str, name: str) -> str:
    try:
        return str(uuid.UUID(value))
    except Exception:
        raise ValueError(f"{name} is not a valid GUID: {value}")

def trigger_power_automate_email(ingestion_id: str, masked_blob_name: str):
    """
    Triggers Power Automate flow to send email notification
    with the masked PDF blob name and ingestion ID.
    """
    try:
        payload = {
            "ingestion_id": ingestion_id,
            "masked_blob_name": masked_blob_name
        }
        
        logger.info(
            "Triggering Power Automate webhook",
            extra={
                "ingestion_id": ingestion_id,
                "masked_blob_name": masked_blob_name
            }
        )
        
        response = requests.post(
            POWER_AUTOMATE_WEBHOOK_URL,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info(
            "Power Automate webhook triggered successfully",
            extra={
                "ingestion_id": ingestion_id,
                "status_code": response.status_code
            }
        )
        
        return True
        
    except requests.exceptions.Timeout:
        logger.error(
            "Power Automate webhook timed out",
            extra={"ingestion_id": ingestion_id}
        )
        return False
        
    except requests.exceptions.RequestException as exc:
        logger.exception(
            "Power Automate webhook call failed",
            extra={
                "ingestion_id": ingestion_id,
                "error": str(exc)
            }
        )
        return False
    
def trigger_power_automate_error(ingestion_id: str, error_stage: str, 
                                 error_message: str, file_name: str):
    """
    Triggers Power Automate flow to send ERROR email notification
    when processing fails.
    """
    if not POWER_AUTOMATE_ERROR_WEBHOOK_URL:
        logger.warning(
            "POWER_AUTOMATE_ERROR_WEBHOOK_URL not configured",
            extra={"ingestion_id": ingestion_id}
        )
        return False
        
    try:
        payload = {
            "ingestion_id": ingestion_id,
            "error_stage": error_stage,
            "error_message": error_message,
            "file_name": file_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Triggering Power Automate ERROR webhook",
            extra={
                "ingestion_id": ingestion_id,
                "error_stage": error_stage
            }
        )
        
        response = requests.post(
            POWER_AUTOMATE_ERROR_WEBHOOK_URL,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info(
            "Power Automate ERROR webhook triggered successfully",
            extra={
                "ingestion_id": ingestion_id,
                "status_code": response.status_code
            }
        )
        
        return True
        
    except requests.exceptions.Timeout:
        logger.error(
            "Power Automate ERROR webhook timed out",
            extra={"ingestion_id": ingestion_id}
        )
        return False
        
    except requests.exceptions.RequestException as exc:
        logger.exception(
            "Power Automate ERROR webhook call failed",
            extra={
                "ingestion_id": ingestion_id,
                "error": str(exc)
            }
        )
        return False
    
def process_pdf(pdf_bytes: bytes, file_name: str, file_id: str | None = None, ingestion_id: str | None = None ):

    current_stage = "INIT"
    po_id = None
    try:
        logger.info(
            "PDF processing started (bytes)",
            extra={
                "filename": file_name,
                "byte_size": len(pdf_bytes)
            }
        )
            
        # Normalize IDs ONLY if provided (Power Automate flow)
        if ingestion_id:
            ingestion_id = normalize_guid(ingestion_id, "IngestionID")
        if file_id:
            file_id = normalize_guid(file_id, "FileID")
        if ingestion_id:
            update_ingestion_status(ingestion_id, "PROCESSING")  

        # ---------------------------------------------------------------------
        # Stage 0 -> Converting Pdf to Bytes
        # ---------------------------------------------------------------------

        # logger.info("Stage 0 | Loading PDF as bytes")

        # pdf_bytes = load_pdf_as_bytes(pdf_name)

        # logger.info(
        #     f"Stage 0 | PDF loaded successfully | size_bytes={len(pdf_bytes)}"
        # )
        # print(f"Loaded PDF ({len(pdf_bytes)} bytes)")

        # ---------------------------------------------------------------------
        # Stage 1 -> LLM Classifier
        # ---------------------------------------------------------------------

        # logger.info("Stage 1 | Running LLM PO classifier on PDF images")
        # current_stage = "STAGE_1_CLASSIFICATION"
        # po_clasify_result = classify_po_pdf_from_images(pdf_bytes)
        # flag = po_clasify_result.Type

        # logger.info(
        #     f"Stage 1 | PO classification completed | type={flag}"
        # )

        # image_list = pdf_bytes_to_images(pdf_bytes) ----> We dont need this 

        # logger.info(
        #     f"Stage 1 | PDF converted to images | image_count={len(image_list)}"
        # )

        # ---------------------------------------------------------------------
        # Stage 2 -> Extract PO As it is
        # ---------------------------------------------------------------------
        # @capture_errors(stage="HEADER_EXTRACTION")
        # logger.info("Stage 2 | Extracting PO Header data from PDF bytes")
        # try:
        #     header_data = extract_POHeader_data_from_bytes(pdf_bytes)

        # except Exception as exc:
        #     print("Header extraction failed:", str(exc))

        #     #INSERT into POHeader table
        #     po_number = header_data.PONumber or "UNKNOWN"

        #     if ingestion_id and file_id:
        #         po_id = insert_po_header(
        #             po_number=po_number,
        #             file_id=file_id,
        #             ingestion_id = ingestion_id,
        #             header_data=header_data
        #         )
        #         logger.info(
        #     "POHeader inserted",
        #     extra={
        #         "po_id": po_id,
        #         "file_id": file_id,
        #         "ingestion_id": ingestion_id
        #     }
        #     )
        #     else:
        #         logger.info(
        #             "Skipping POHeader insert — local / non-ingestion flow",
        #             extra={"filename": file_name}
        # )
        logger.info("Stage 1 | Extracting all medicine names from OCR Result of Layout")

        logger.info( "Stage 1 | Extracting the layout using prebuilt-layout")
        current_stage = "STAGE_1_LAYOUT_EXTRACTION"
        ocr_text,result = get_layout_result(pdf_bytes)

        logger.info( " Stage 1 | Extracting the medicine names for the layout result")
        all_medicine_list = medicine_names_layout(ocr_text)

        logger.info(
            f"Stage 1 | Medicine extraction completed | total_medicines={len(all_medicine_list)}"
        )

        non_gsk_med_list = filter_non_gsk_medicines(all_medicine_list, GSK_BRANDS)
        print("all medicine:")
        for med in all_medicine_list:
            print( med )
        print ( "Non gsk medicine: ********************")
        for non in non_gsk_med_list:
            print( non)
        print ( "********************")

        logger.info(
            f"Stage 1 | Non-GSK filtering completed | non_gsk_count={len(non_gsk_med_list)}"
        )

        # ---------------------------------------------------------------------
        # Stage 1.2 -> Build layout index for NON-GSK medicines (NEW)
        # ---------------------------------------------------------------------

        logger.info(
            "Stage 2.5 | Building layout index for NON-GSK medicines (fallback prep)"
        )

        layout_index = build_layout_index_for_non_gsk(
            layout_result=result,
            non_gsk_med_list=non_gsk_med_list,
        )

        logger.info(
            "Stage 2.5 | Layout index built | medicines_indexed=%d",
            len(layout_index)
        )

        print ( "********* Layout Indexing Result **********")
        for med in layout_index:

            logger.info("Layout-indexed NON-GSK medicine | %s", med)

        print ( "********************")

        fallback_spans = set()

        for norm_med, entries in layout_index.items():
            for entry in entries:
                fallback_spans.add((
                    entry["page_no"],
                    entry["y1"],
                    entry["y2"]
                ))
 

        logger.info("Stage 2 | Extracting PO Header data from PDF bytes")

        try:
            current_stage = "STAGE_2_HEADER_EXTRACTION"
            header_data = extract_POHeader_data_from_bytes(pdf_bytes)

            po_number = header_data.PONumber or "UNKNOWN"

            if ingestion_id and file_id:
                current_stage = "STAGE_2_HEADER_INSERTION"
                po_id = insert_po_header(
                    po_number=po_number,
                    file_id=file_id,
                    ingestion_id=ingestion_id,
                    header_data=header_data,
                )

                logger.info(
                    "POHeader inserted",
                    extra={
                        "po_id": po_id,
                        "file_id": file_id,
                        "ingestion_id": ingestion_id
                    }
                )
            else:
                logger.info("Skipping POHeader insertion — local / non-ingestion flow",
                            extra={"filename": file_name}
                            )

        except Exception as exc:
            raise RuntimeError("POHeader extraction / insertion failed") from exc
        

            # logger.exception(
            #     "Stage 2 | PO Header extraction failed",
            #     extra={
            #         "file_name": file_name,
            #         "ingestion_id": ingestion_id,
            #         "file_id": file_id
            #     }
            # )


        # logger.info("Stage 2 | Extracting all medicine names from images")

        # # -------------------->

        # all_medicine_list = extract_all_medicines_from_images(image_list)

        # logger.info(
        #     f"Stage 2 | Medicine extraction completed | total_medicines={len(all_medicine_list)}"
        # )

        # non_gsk_med_list, gsk_med_list = filter_non_gsk_medicines(all_medicine_list, GSK_BRANDS)

        # print ( "Non gsk medicine: ********************")
        # for non in non_gsk_med_list:
        #     print( non)
        # print ( "********************")

        # print ("GSK medicine: ********************")
        # for gsk in gsk_med_list:
        #     print( gsk)
        # print ( "********************")
        

        # logger.info(
        #     f"Stage 2 | Non-GSK filtering completed | non_gsk_count={len(non_gsk_med_list)}"
        # )
        

        # ---------------------------------------------------------------------
        # Stage 3 -> PO Item Extraction
        # ---------------------------------------------------------------------

        logger.info("Stage 3 | Extracting structured PO item list")
        current_stage = "STAGE_3_PO_ITEM_EXTRACTION"
        poItemList= extract_po_items_from_pdf_pages(ocr_text)

        logger.info("Stage 3 | Extracted PO Items:")

        for idx, item in enumerate(poItemList.items, start=1):
            logger.info(
                "Item %d | Product=%s | Qty=%s | UOM=%s | Price=%s | HSN=%s",
                idx,
                item.ProductDescription,
                item.Quantity,
                item.UnitOfMeasure,
                item.Price,
                item.HSNCode
            )
        
        # -------------------------------------------------------------------------
        # INSERT PO ITEMS (DATA IS FINAL AT THIS POINT)
        # -------------------------------------------------------------------------
        if ingestion_id and file_id and po_id:
            try:
                current_stage = "STAGE_3_PO_ITEM_INSERTION"
                logger.info(
                    "Starting POItem insertion",
                    extra={
                        "po_id": po_id,
                        "total_rows": len(poItemList.items)
                    }
                )

                filtered_po_items = [
                    item for item in poItemList.items
                    if any(
                    brand.upper() in (item.ProductDescription or "").upper()
                    for brand in GSK_BRANDS
                    )
                ]


                inserted_count = insert_po_items(
                    po_id=po_id,
                    items=filtered_po_items
                )

                logger.info(
                    "POItem insertion completed",
                    extra={
                        "po_id": po_id,
                        "inserted_count": inserted_count
                    }
                )

            except Exception as exc:
                # logger.exception(
                #     "POItem insertion failed",
                #     extra={"po_id": po_id}
                # )
                raise RuntimeError("POItem insertion failed") from exc
        else:
            logger.info(
                "Skipping POItem insertion — missing po_id / ingestion flow",
                extra={
                    "filename": file_name,
                    "po_id": po_id
                }
            )


        # ---------------------------------------------------------------------
        # Stage 4 -> PDF Bytes to ocr result & Grid formation
        # ---------------------------------------------------------------------

        logger.info("Stage 4 | Running OCR engine on PDF bytes")
        current_stage = "STAGE_4_OCR_PROCESSING"
        ocr_result = run_adi_ocr(pdf_bytes)

        logger.info(
            "Stage 4 | OCR completed | extracting tables metadata"
        )

        tables_raw = ocr_result.get("tables", [])

        ##################################### Debugging ###################################

        if not tables_raw:
            logger.warning("Stage 4 | No OCR tables found")
        else:
            logger.info("Stage 4 | Dumping ALL OCR tables for inspection")

            for t_idx, table in enumerate(tables_raw):
                logger.info(
                    "TABLE %d | row_count=%s | column_count=%s | cell_count=%d",
                    t_idx,
                    table.get("row_count"),
                    table.get("column_count"),
                    len(table.get("cells", [])),
                )

                for c_idx, cell in enumerate(table.get("cells", []), start=1):
                    page_no = None
                    if cell.get("bounding_regions"):
                        page_no = cell["bounding_regions"][0].get("page_number")

                    logger.info(
                        "  T%d-C%d | row=%s col=%s | page=%s | text=%r",
                        t_idx,
                        c_idx,
                        cell.get("row_index"),
                        cell.get("column_index"),
                        page_no,
                        cell.get("content"),
                    )


        ##################################### Debugging ###################################

        logger.info(
            f"Stage 4 | OCR tables detected | table_count={len(tables_raw)}"
        )

        logger.info(
            "Stage 4 | Evaluating OCR tables for PO relevance (grid + markdown + LLM)"
        )

        tables = evaluate_tables_for_po(ocr_result["tables"])

        po_table_count = sum(1 for t in tables.tables if t.is_po)

        print( tables )
        logger.info(
            f"Stage 4 | Table evaluation completed | po_tables={po_table_count} | total_tables={len(tables.tables)}"
        )

        # ---------------------------------------------------------------------
        # Stage 5 ->  Finding Coordinates
        # ---------------------------------------------------------------------

        logger.info("Stage 5 | Entering coordinates finding phase")

        all_matched_cells = set()

        # --------------------> Finding the Min_X and Max_X coordinates <-------------------------------


        # -------------------------------------------------
        # STEP 1: Get FIRST PO table evaluation
        # -------------------------------------------------

        first_po_table = next(
            (t for t in tables.tables if t.is_po),
            None
        )

        if first_po_table is None:
            logger.warning("Stage 5 | No PO tables found — skipping coordinate extraction")
            # sys.exit(0)
            raise RuntimeError("No PO tables found in document")


        logger.info(
            "Stage 5 | First PO table identified | table_index=%d | page=%d",
            first_po_table.table_index,
            first_po_table.page_number
        )

        # -------------------------------------------------
        # STEP 2: Navigate back to OCR table using index
        # -------------------------------------------------

        first_ocr_table = ocr_result["tables"][first_po_table.table_index]

        # -------------------------------------------------
        # STEP 3: Compute global X bounds for PO tables
        # -------------------------------------------------

        x_min, x_max = get_table_x_bounds(first_ocr_table)

        logger.info(
            "Stage 5 | PO table X bounds calculated | x_min=%.2f | x_max=%.2f",
            x_min,
            x_max
        )


        for table in tables.tables:

            # Only PO tables are relevant
            if not table.is_po:
                continue

            # If medicine column was not identified, skip safely
            if table.med_col_idx is None:
                logger.warning(
                    "Skipping table %d (page %d) — med_col_idx not found",
                    table.table_index,
                    table.page_number
                )
                continue

            logger.info(
                "Stage 5 | Scanning table %d on page %d (med_col_idx=%d)",
                table.table_index,
                table.page_number,
                table.med_col_idx
            )

            ocr_table = ocr_result["tables"][table.table_index]

            # grid_idx, start_row, end_row = find_non_gsk_row_spans(
            #     po_grid = table.grid,
            #     ocr_table=ocr_table,
            #     med_col_idx=table.med_col_idx,
            #     non_gsk_med_list=non_gsk_med_list,
            #     grid_idx = table.table_index
            # )

            # if start_row is not None:
            #     all_matched_cells.add((grid_idx, start_row, end_row))

            # spans = find_non_gsk_row_spans(
            # po_grid=table.grid,
            # ocr_table=ocr_table,
            # med_col_idx=table.med_col_idx,
            # non_gsk_med_list=non_gsk_med_list,
            # grid_idx=table.table_index
            # )

            print("Non GSK products:")
            for non_gsk in non_gsk_med_list:
                print(non_gsk)
            print("*"*50)
            spans = find_fragmented_match(
                po_grid=table.grid,
                med_col_idx=table.med_col_idx,
                non_gsk_med_list=non_gsk_med_list,
                header_rows=table.header_rows,
            )

            logger.info(
            "Stage 5 | Returned spans from matcher | table=%d | spans=%s",
            table.table_index,
            spans
            )

            for (start_row, end_row) in spans:
                grid_idx = table.table_index
                logger.info(
                    "Adding matched span | table=%d | start_row=%d | end_row=%d",
                    grid_idx, start_row, end_row
                )
                all_matched_cells.add((grid_idx, start_row, end_row))

            # all_matched_cells.update(matched)

        logger.info(
            "Stage 5 | Non-GSK medicine cells identified | count=%d",
            len(all_matched_cells)
        )

        for grid_idx, start_row, end_row in sorted(all_matched_cells):
            logger.info(
                "Non-GSK Medicine Span → table_index=%d | start_row=%d | end_row=%d",
                grid_idx,
                start_row,
                end_row
            )
        



        y_spans = set()

        for (grid_idx, start_row, end_row) in all_matched_cells:

        #     logger.info(
        #         "Y-SPAN REQUEST | table=%d | start_row=%d | end_row=%d",
        #         grid_idx,
        #         start_row,
        #         end_row
        #     )

            # 1. Get Y bounds from OCR
            y1, y2 = get_y1_y2_from_ocr(
                ocr_tables=ocr_result["tables"],
                grid_idx=grid_idx,
                start_row=start_row,
                end_row=end_row
            )

            logger.info(
                "Y-SPAN RESULT | table=%d | start_row=%d | end_row=%d | y1=%.4f | y2=%.4f",
                grid_idx,
                start_row,
                end_row,
                y1 if y1 is not None else -1,
                y2 if y2 is not None else -1
            )

            # 2. Resolve page number via Pydantic table
            table_eval = next(
                t for t in tables.tables if t.table_index == grid_idx
            )

            page_no = table_eval.page_number - 1  # fitz is 0-based

            logger.info(
                "PAGE RESOLUTION | table=%d | pydantic_page=%d | fitz_page=%d",
                grid_idx,
                table_eval.page_number,
                page_no
            )

            # 3. Store span
            y_spans.add((page_no, y1, y2))

            logger.info(
                "FINAL REDACTION SPAN | page=%d | x1=%.2f | x2=%.2f | y1=%.4f | y2=%.4f",
                page_no,
                x_min,
                x_max,
                y1,
                y2
            )

        y_spans |= fallback_spans

        logger.info("========== REDACTION INPUT DUMP ==========")

        logger.info("X-BOUNDS | x1=%.2f | x2=%.2f", x_min, x_max)

        for page_no, y1, y2 in sorted(y_spans):
            logger.info(
                "REDACT SPAN | page=%d | x1=%.2f | x2=%.2f | y1=%.2f | y2=%.2f",
                page_no, x_min, x_max, y1, y2
            )

        logger.info("========== END REDACTION INPUT ==========")


        current_stage = "STAGE_5_REDACTION_GENERATION"
        redacted_pdf_bytes=redact_pdf_from_stream_with_spans(
            pdf_stream=pdf_bytes,
            x1=x_min,
            x2=x_max,
            y_spans=y_spans
        )
        logger.info(
            "Stage 5 | Redacted PDF generated",
            extra={"output_path": f"REDACTED_OUTPUT/{file_name}"}
        )
        # -------------------------------------------------------------------------
            # UPLOAD MASKED PDF + INSERT DB RECORD
            # -------------------------------------------------------------------------
        if ingestion_id and file_id:
            try:
                masked_blob_name = build_masked_blob_name(
                    file_id=file_id,
                    original_file_name=file_name
                )
                current_stage = "FINAL_MASKED_FILE_UPLOAD"
                upload_bytes_to_blob(
                    container_name="maskedpdfs",
                    blob_name=masked_blob_name,
                    data=redacted_pdf_bytes
                )
                masked_file_id = insert_masked_file(
                    file_id=file_id,
                    masked_blob_name=masked_blob_name
                )
                logger.info(
                    "Masked PDF uploaded and DB record created",
                    extra={
                        "file_id": file_id,
                        "masked_file_id": masked_file_id,
                        "blob_name": masked_blob_name
                    }
                )
                # Trigger Power Automate email notification
                trigger_power_automate_email(
                    ingestion_id=ingestion_id,
                    masked_blob_name=masked_blob_name
                )
            except Exception as exc:
                logger.exception(
                    "Masked file upload / DB insert failed",
                    extra={"file_id": file_id}
                )
                raise RuntimeError("Masked file persistence failed") from exc
        else:
            logger.info(
                "Skipping masked file persistence — local / non-ingestion flow",
                extra={"filename": file_name}
            )
        if ingestion_id:
            update_ingestion_status(ingestion_id, "COMPLETED")
    
    # except Exception as exc:
    #     # -----------------------------------------
    #     # AUTO FAILURE -> ERROR
    #     # -----------------------------------------
    #     if ingestion_id:
    #         update_ingestion_status(ingestion_id, "ERROR")

    #     logger.exception(
    #         "PDF processing failed",
    #         extra={
    #             "filename": file_name,
    #             "ingestion_id": ingestion_id,
    #             "file_id": file_id
    #         }
    #     )
    #     raise
    except Exception as exc:
        error_message = str(exc)
    # -------------------------------
    # 1. Update ingestion status
    # -------------------------------
        if ingestion_id:
            try:
                update_ingestion_status(ingestion_id, "ERROR")
            except Exception as status_exc:
                logger.exception("Failed to update ingestion status to ERROR")

            try:

                # -------------------------------
                # 2. Persist failure to DB
                # -------------------------------
                log_processing_failure(
                    error=exc,
                    category="PIPELINE_ERROR",
                    stage=current_stage,
                    ingestion_id=ingestion_id,
                    file_id=file_id,
                    filename=file_name
                )
            except Exception as db_exc:
                logger.exception("Failed to log processing failure to DB")
            try:
                trigger_power_automate_error(
                    ingestion_id=ingestion_id,
                    error_stage=current_stage,
                    error_message=error_message,
                    file_name=file_name
                )
            except Exception as notify_exc:
                logger.exception("Failed to trigger Power Automate error notification")

        # -------------------------------
        # 3. Log for developers
        # -------------------------------
        logger.exception(
            "PDF processing failed",
            extra={
                "filename": file_name,
                "ingestion_id": ingestion_id,
                "file_id": file_id,
                "stage": current_stage
            }
        )

        raise
