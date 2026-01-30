import os
from dotenv import load_dotenv
from utils.stage0.pdf_to_bytes import load_pdf_as_bytes
import sys
from openai import AzureOpenAI
from pydantic import BaseModel
from models.po_models import MedicineList
import json


from utils.logging.logger import get_logger


logger = get_logger(__name__)
load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")


def medicine_names_layout(ocr_text):

    SYSTEM_PROMPT = """
    You are an expert in analyzing Purchase Orders extracted via OCR.

Your task is to extract ALL item names exactly as they appear in the document.

Important:

- Item names may be split across multiple lines due to formatting.
- You MUST merge ONLY when a line is clearly a continuation of the same name
  (for example when words are broken or wrapped mid-sentence).

- HOWEVER:

If two consecutive lines look like complete medicine names (even if similar):
→ Treat them as SEPARATE items
→ DO NOT merge them

Examples to keep separate:

ACITROM 1 MG TAB
ACITROM 1 MG TABLET

AUGMENTIN 1.2 GM/VIAL INJ
AUGMENTIN 1.2 GM/VIAL POWDER FOR INJECTION

ATORLIP 20MG TABLET 15'S - CIPLA
ATORLIP 20MG TABLET 15'S (ATORVASTATIN 20MG) - CIPLA

---

Rules:

- Use table structure (QTY, UOM, PRICE columns) to identify item rows.
- Preserve exact OCR text (case, spacing, symbols).
- Do NOT normalize or correct spelling.
- Do NOT remove duplicates (even across pages).
- If the same medicine appears again later, include it again.
- Item names may contain packing patterns, brackets, numbers, symbols.

Additional rule:

- If alphanumeric tokens such as INJ0863, TAB14387, CAP1023, etc appear
  immediately after or within the Item Name column, treat them as PART of
  the medicine name and include them in the extracted name.
- Return an empty list if no items are found.
- Do not include pure UOM values such as STRIP10, EACH, NOS, VIAL if they appear
  as a separate unit column.
- Keep pack-size expressions like (1X14), 10'S, TAB14 ,1*10 as part of item name.



Return ALL item names as individual entries.

Return empty list if none found.

Return ONLY JSON in provided schema.
    """



    user_prompt = f"""
    Below is OCR text extracted from a Purchase Order.

    The item names may be broken across multiple lines.
    Your job is to reconstruct the FULL item names exactly as they appear.

    OCR_text:
    {ocr_text}

    Schema:
    {json.dumps(MedicineList.model_json_schema(), indent=2)}

    Return ONLY the JSON object in the given schema.
    """

    response = client.chat.completions.parse(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        response_format=MedicineList,
    )

    parsed = response.choices[0].message.parsed
    medicine_names = parsed.MedicineListName

    return medicine_names

if __name__ == "__main__":
    pdf_path = sys.argv[1]         
    pdf_bytes = load_pdf_as_bytes(pdf_path)

    medicine_names = medicine_names_layout(pdf_bytes)

    print(medicine_names)
    print("Total items:", len(medicine_names)) 



#     # You are an expert in analyzing Purchase Orders extracted via OCR.

# # Your task is to extract the FULL item names from the document.

# # Important:
# # - Item names may be split across multiple lines due to formatting.
# # - You MUST intelligently combine wrapped lines that belong to the same item.
# # - Use surrounding context such as quantity, UOM, rate, and price columns to detect item rows.
# # - The final name should represent the complete product description.
# # - Item names may include numbers, symbols, and packing patterns such as 1*10, 1*15, 1*20, 60 TAB 1*10, 1*300ML,(1X14) etc — treat them as part of the item name and DO NOT drop them.

# # Rules:
# # - Do NOT normalize, expand, or correct spelling.
# # - Keep the text exactly as it appears (case, spacing, symbols).
# # - Do NOT hallucinate missing words.
# # - If an item name is split across lines, merge them logically (including numeric/symbol parts).
# # - Include duplicates if present.
# # - Return an empty list if no items are found.


# """