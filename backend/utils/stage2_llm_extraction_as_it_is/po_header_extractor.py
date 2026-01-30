
from utils.logging.logger import get_logger
from utils.stage2_llm_extraction_as_it_is.llm_extraction_0 import extract_header_from_text
from utils.stage2_llm_extraction_as_it_is.ocr_check_1 import extract_pdf_data_from_bytes

logger = get_logger(__name__)


def extract_POHeader_data_from_bytes(pdf_bytes: bytes):
    logger.info(
        "Header extraction started (bytes)",
        extra={"byte_size": len(pdf_bytes)}
    )

    ocr_text = extract_pdf_data_from_bytes(pdf_bytes)

    logger.info(
        "OCR text extracted",
        extra={"text_length": len(ocr_text)}
    )

    header_data = extract_header_from_text(ocr_text)

    # Here this is the hospital name that we will be extracting
    hosp_name = header_data.HospitalName
    # hosp_addr = header_data.HospitalLocation
    po_date = header_data.PODate

    logger.info(
        "Hospital extracted from PO header",
        extra={
            "hospital_name": hosp_name,
            # "hospital_address": hosp_addr,
            "po_date": str(po_date)
        }
    )

    # hospital_details = extract_city_state_from_address(hosp_addr)

    # city = hospital_details.City
    # state = hospital_details.State



    logger.info(
        "Header extraction completed",
        extra={"header_fields": list(header_data.model_dump().keys())}
    )

    return header_data

