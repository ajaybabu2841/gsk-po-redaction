import os
import re
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
# from utils.logging.decorators import capture_errors
# from utils.logging.error_handler import log_pipeline_errors
from utils.stage1_llm_classifier.llm_classifier import client, DEPLOYMENT_NAME
# Load credentials
load_dotenv()

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

# Initialize client
client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# @capture_errors(stage="OCR_EXTRACTION")
# @log_pipeline_errors(stage="OCR_EXTRACTION")
# def extract_pdf_data(file_path):
#     """Extracts all text and structured data from a PDF using Azure Document Intelligence."""

#     with open(file_path, "rb") as f:
#         file_data = f.read()

#         poller = client.begin_analyze_document(
#         model_id="prebuilt-read",
#         body=AnalyzeDocumentRequest(bytes_source=file_data)
#     )
#     result = poller.result()
#     ocr_text = "\n".join([line.content for page in result.pages for line in page.lines])
#     return ocr_text

# @capture_errors(stage="OCR_EXTRACTION")
# @log_pipeline_errors(stage="OCR_EXTRACTION")
def extract_pdf_data_from_bytes(pdf_bytes: bytes):
    """
    Extracts all text from PDF bytes using Azure Document Intelligence.
    Cloud-safe, no filesystem usage.
    Includes preprocessing to fix common OCR issues.
    """

    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        body=AnalyzeDocumentRequest(bytes_source=pdf_bytes)
    )

    result = poller.result()

    # ocr_text = "\n".join(
    #     [line.content for page in result.pages for line in page.lines]
    # )

    # # Preprocess to fix common issues (split PO numbers, etc.)
    # ocr_text = preprocess_ocr_text(ocr_text)

    # return ocr_text
    page1_text = "\n".join(
        line.content for line in result.pages[0].lines
    )

    return preprocess_ocr_text(page1_text)


def preprocess_ocr_text(text: str) -> str:
    """
    Preprocess OCR text to fix common issues:
    - Join split PO numbers across lines
    - Fix common OCR artifacts
    - Normalize spacing
    """
    # Join PO numbers split across lines
    # Pattern: "PO Number: ABC123/" on one line, "XYZ456" on next line
    text = re.sub(
        r'(PO[:\s#]*[A-Z0-9\-/]+)/\s*\n\s*([A-Z0-9\-/]+)',
        r'\1/\2',
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Join when PO label and number are on separate lines
    text = re.sub(
        r'(P\.?O\.?\s*(?:Number|No\.?|#)?:?)\s*\n\s*([A-Z0-9][A-Z0-9\-/]+)',
        r'\1 \2',
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Join POIP style numbers split across lines
    text = re.sub(
        r'(POIP[0-9\-]*)\s*\n\s*([0-9\-]+)',
        r'\1\2',
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Join long numeric sequences split across lines (8+ digits)
    text = re.sub(
        r'(\d{4,})\s*\n\s*(\d{4,})',
        r'\1\2',
        text,
        flags=re.MULTILINE
    )
    
    return text


def extract_po_number_hints(text: str) -> list:
    """
    Extract potential PO number candidates using regex patterns.
    Returns list of candidates to help LLM focus.
    """
    candidates = []
    
    # Pattern 1: Explicit PO Number label
    pattern1 = r'(?:PO|Purchase\s*Order)\s*(?:Number|No\.?|#)?[:\s]*([A-Z0-9][A-Z0-9\-/]{2,})'
    matches = re.findall(pattern1, text, re.IGNORECASE)
    candidates.extend(matches)
    
    # Pattern 2: POIP style
    pattern2 = r'(POIP[0-9\-]+)'
    matches = re.findall(pattern2, text, re.IGNORECASE)
    candidates.extend(matches)
    
    # Pattern 3: Long numeric PO numbers (8-12 digits)
    pattern3 = r'(?:PO|Order)[:\s#]*([0-9]{8,12})'
    matches = re.findall(pattern3, text, re.IGNORECASE)
    candidates.extend(matches)
    
    # Remove duplicates and return
    return list(set(candidates))[:5]  # Top 5 candidates 