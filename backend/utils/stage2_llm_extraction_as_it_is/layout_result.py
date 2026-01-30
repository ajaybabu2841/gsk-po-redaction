import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from utils.logging.logger import get_logger

# -------------- Initializing the values ------------------------
logger = get_logger(__name__)

load_dotenv()

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

clientadi = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# ------------------- Starting the ADI layout extraction -----------------------

def get_layout_result(pdf_bytes):

    poller = clientadi.begin_analyze_document(
    model_id="prebuilt-layout",
    body=AnalyzeDocumentRequest(bytes_source=pdf_bytes)
    )

    result = poller.result()
    ocr_text = "\n".join([line.content for page in result.pages for line in page.lines])

    return ocr_text,result