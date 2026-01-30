#llm_extraction
import os
import json
import re
from models.po_models import POHeader
# from utils.logging.decorators import capture_errors
from utils.logging.error_handler import log_pipeline_errors
from utils.stage1_llm_classifier.llm_classifier import client, DEPLOYMENT_NAME
from utils.logging.logger import get_logger
from utils.stage2_llm_extraction_as_it_is.ocr_check_1 import extract_po_number_hints

logger = get_logger(__name__)



# @log_pipeline_errors(stage="HEADER_LLM_EXTRACTION_PHASE1")
def extract_critical_fields(ocr_text: str) -> dict:
    """
    Phase 1: Universal extraction using pure semantic reasoning.
    Extracts PONumber, PODate, HospitalName, AWDName.
    NOTE: ocr_text here always refers to PAGE 1 OCR text only.
    """
    
    po_hints = extract_po_number_hints(ocr_text)
    hints_text = ""
    if po_hints:
        hints_text = f"""

PATTERN-DETECTED CANDIDATES (unverified - use semantic judgment):
{chr(10).join(f"  • {hint}" for hint in po_hints[:10])}

These are raw patterns. Validate each semantically."""
    
    system_prompt = """You are an expert Purchase Order document analyst.
    Extract information using semantic meaning, not exact label matching.
    Prefer complete, authoritative values.
    Return only valid JSON. No explanation."""


    user_prompt = f"""Extract the four key header fields from this Purchase Order using semantic reasoning.

SEMANTIC EXTRACTION RULES (CRITICAL):

GENERAL:
- Understand what each value REPRESENTS in the business transaction
- Prefer document-level identifiers over references, versions, or component numbers
- Prefer complete forms over partial or abbreviated ones
- If genuinely uncertain, return null

PONumber (Primary Transaction Identifier):
- This uniquely identifies the entire transaction
- Do NOT confuse with:
  - Version numbers
  - Product codes
  - Dates
- Financial-year formatted PO numbers like "25-26/4908" ARE VALID PO NUMBERS
- Do NOT treat financial year prefixes as dates or versions
- If PO Version is shown as a SEPARATE field, DO NOT append it to the PO Number
- Prefer the most complete and authoritative representation

IMPORTANT:
- If the PO Number appears with an alphanumeric prefix (e.g., MHK-, MHRN-, HOSP-, PO-),
  the prefix is PART OF THE IDENTIFIER and MUST be retained
- Never strip organizational prefixes unless they are clearly labels
- Prefer "PREFIX-NUMBER" over bare numeric values when both appear


Buyer (HospitalName):
- Organization that is ACQUIRING / RECEIVING goods or services
- Money flows FROM this party
- Extract only the ORGANIZATION NAME (not address, contact, or department text)

Seller (AWDName):
- Organization that is SUPPLYING / PROVIDING goods or services
- Money flows TO this party
- Extract only the ORGANIZATION NAME (not address or contact details)

PODate:
- Date when the Purchase Order was issued
- Format: YYYY-MM-DD

{hints_text}

DOCUMENT TEXT (Page 1):
{ocr_text}

Return ONLY this JSON structure:

{{
  "PONumber": "string or null",
  "PODate": "YYYY-MM-DD or null",
  "HospitalName": "string or null",
  "AWDName": "string or null"
}}"""


    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        usage = response.usage
        result = json.loads(response.choices[0].message.content)
        logger.info(
        "Phase 1 LLM usage",
        extra={
            "stage": "HEADER_LLM_EXTRACTION_PHASE1",
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "po_number": result.get("PONumber")
            }
        )

        logger.info(
            "Phase 1 extraction completed",
            extra={
                "po_number": result.get("PONumber"),
                "po_date": result.get("PODate"),
                "hospital": result.get("HospitalName"),
                "AWDName": result.get("AWDName"),
                "hints_provided": len(po_hints) if po_hints else 0
            }
        )
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {
            "PONumber": None,
            "PODate": None,
            "HospitalName": None,
            "AWDName": None
        }
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise




@log_pipeline_errors(stage="HEADER_LLM_EXTRACTION_PHASE2")
def extract_remaining_fields(ocr_text: str, critical_fields: dict) -> dict:
    """
    Phase 2: Extract remaining fields with context from Phase 1.
    This reduces LLM confusion by providing already-identified fields.
    """
    
    po_number = critical_fields.get("PONumber", "UNKNOWN")
    hospital = critical_fields.get("HospitalName", "UNKNOWN")
    vendor = critical_fields.get("AWDName", "UNKNOWN")
    po_date = critical_fields.get("PODate", "UNKNOWN")
    
    system_prompt = """You are an expert document analyst with years of experience reading Indian Purchase Order documents.
Use context and semantic understanding, not just exact label matching.
Field names vary across organizations - focus on what the information REPRESENTS."""

    user_prompt = f"""Continue extracting remaining fields from this Purchase Order document.

ALREADY IDENTIFIED (for context):
- Purchase Order Number: {po_number}
- PO Issue Date: {po_date}
- Buyer/Hospital: {hospital}
- Vendor/Supplier: {vendor}

 CRITICAL INSTRUCTION FOR VendorGSTIN:
Extract the GSTIN that belongs to the VENDOR/SUPPLIER: "{vendor}"

DO NOT extract:
- Hospital GSTN# / Buyer GSTN#
- Customer GSTN#
- Bill To GSTN#
- Any GSTIN labeled as belonging to "{hospital}"

ONLY extract:
- Vendor GSTN# / Vendor GTIN# / Supplier GSTN#
- Party GSTN# (if party refers to vendor)
- Seller GSTN#
- The GSTIN explicitly labeled as "Vendor GSTN#" or near the vendor name "{vendor}"


Now extract the following fields. Think semantically - labels may vary:

**Vendor Information:**
- VendorGSTIN: Vendor's 15-character GST Identification Number (format: 22AAAAA0000A1Z5). Look for "Vendor GSTN", "Supplier GST", "Party GSTIN" near the vendor section "{vendor}". Do NOT use Hospital/Buyer GSTIN.
- VendorCode: The code/ID assigned to this vendor by the hospital. Could be "Vendor Code", "Supplier Code", "Party Code".
- Supplier_AWD: Full supplier details block (name, address, contact combined).

**Dates (all in YYYY-MM-DD format):**
- POApprovalDate: When was this PO approved? Could be "Approved Date", "Authorization Date". May differ from PO issue date.
- RCValidityDate: Rate Contract expiry date. Could be "RC Valid Upto", "RC Expiry", "Valid Till".
- RC_Validity_From: Rate Contract start date. Could be "RC Valid From", "RC Start Date", "Effective From".

**Rate Contract:**
- RCNumber: Rate Contract number. Could be "RC No", "Rate Contract No", "Contract No", "Agreement No".
- RC_Rate: Rate Contract rate/price.

**Hospital/Buyer Information:**
- HospitalLocation: Full hospital address (street, city, state, PIN). Usually in "Buyer Address", "Bill To", "Ship To" section.
- HospitalId: Hospital code/ID if mentioned.

EXTRACTION RULES:
- Return null if field not found (don't guess)
- All dates must be YYYY-MM-DD format
- For VendorGSTIN: Extract the GSTIN belonging to the VENDOR "{vendor}", NOT the hospital
- Remember: "{hospital}" is the BUYER, "{vendor}" is the SUPPLIER
- Numbers should be numeric (int/float), not strings

OCR TEXT (Page 1):
{ocr_text}

Return ONLY a JSON object with these exact field names."""

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    usage = response.usage
    
    result =  json.loads(response.choices[0].message.content)
    logger.info(
    "Phase 2 LLM usage",
    extra={
        "stage": "HEADER_LLM_EXTRACTION_PHASE2",
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "vendor": critical_fields.get("AWDName"),
    }
)
    return result

# @log_pipeline_errors(stage="HEADER_LLM_EXTRACTION")
def extract_header_from_text(ocr_text: str) -> POHeader:
    """Two-phase header extraction for improved accuracy."""
    
    # Phase 1: Critical fields (PO Number, Date, Hospital, Vendor)
    page1_text = ocr_text
    critical_fields = extract_critical_fields(page1_text)

    
    # Phase 2: Remaining fields
    remaining_fields = extract_remaining_fields(page1_text, critical_fields)
    
    # Merge results (Phase 1 takes precedence)
    final_data = {**remaining_fields, **critical_fields}
    
    # Clean and validate PO Number
    po_number = final_data.get("PONumber")
    if po_number:
        po_number = _clean_po_number(po_number)
        final_data["PONumber"] = po_number
    
    # Sanitize data - convert any dicts/lists to strings
    final_data = _sanitize_llm_output(final_data)
    
    logger.info(
        "Header extraction completed",
        extra={
            "po_number": po_number,
            "VendorGSTIN": final_data.get("VendorGSTIN", None),
            "HospitalName": final_data.get("HospitalName", None),
            "AWDName": final_data.get("AWDName", None),
            "PODate": final_data.get("PODate", None),
            "POApprovalDate": final_data.get("POApprovalDate", None),
            "VendorCode": final_data.get("VendorCode", None),
            "HospitalId": final_data.get("HospitalId", None),
            "RCNumber": final_data.get("RCNumber", None),
            "fields_extracted": sum(0 for v in final_data.values() if v is not None)
        }
    )
    
    
    # Validate with Pydantic
    return POHeader.model_validate(final_data)


def _clean_po_number(po_number: str) -> str:
    if not po_number:
        return None

    cleaned = po_number.strip()

    cleaned = re.sub(
        r'^(PO\s*(?:Number|No\.?|#)\s*[:\-]\s*)',
        '',
        cleaned,
        flags=re.IGNORECASE
    )

    return cleaned.strip() or None

ID_FIELDS = {
    "VendorCode",
    "HospitalId",
    "Product_Code",
    "RCNumber",
    "PONumber",
}

def _sanitize_llm_output(data: dict) -> dict:
    """
    Sanitize LLM output to ensure all fields match expected types.
    Converts dicts/lists to strings and normalizes ID fields.
    """
    sanitized = {}

    for key, value in data.items():
        if value is None:
            sanitized[key] = None

        #  FORCE identifiers to string
        elif key in ID_FIELDS:
            sanitized[key] = str(value)

        elif isinstance(value, dict):
            if 'Name' in value or 'Address' in value:
                parts = [str(v) for v in value.values() if v]
                sanitized[key] = ", ".join(parts)
            else:
                sanitized[key] = json.dumps(value)

        elif isinstance(value, list):
            sanitized[key] = ", ".join(str(item) for item in value)

        else:
            sanitized[key] = value

    return sanitized
 
