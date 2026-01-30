import os
import json
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

if not ENDPOINT or not KEY:
    raise RuntimeError("ADI credentials not found in .env")


def run_adi_ocr(pdf_bytes: bytes):
    """
    Runs Azure Document Intelligence OCR (prebuilt-layout)
    and saves BOTH table cells and page lines to JSON.
    """

    client = DocumentIntelligenceClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(KEY),
    )

    # with open(pdf_path, "rb") as f:
    #     pdf_bytes = f.read()

    print("🔹 Running ADI OCR (prebuilt-layout)...")

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes
    )

    result = poller.result()

    tables = []
    
    for table in result.tables:
        table_obj = {
            "row_count": table.row_count,
            "column_count": table.column_count,
            "cells": []
        }

        for cell in table.cells:
            cell_obj = {
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                "content": cell.content,
                "bounding_regions": []
            }

            if cell.bounding_regions:
                for region in cell.bounding_regions:
                    cell_obj["bounding_regions"].append({
                        "page_number": region.page_number,
                        "polygon": region.polygon
                    })

            table_obj["cells"].append(cell_obj)

        tables.append(table_obj)

    # os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

    # with open(output_json_path, "w", encoding="utf-8") as f:
    #     json.dump(tables, f, indent=2)

    # print(f"✅ ADI OCR JSON saved to: {output_json_path}")
    return {
        "tables" : tables
    }
 