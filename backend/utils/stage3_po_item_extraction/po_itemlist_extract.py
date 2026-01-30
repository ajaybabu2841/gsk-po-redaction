# from pydantic import BaseModel, Field
# from openai import AzureOpenAI
# from models.po_models import POItemList
# import os, io, base64 # PyMuPDF
# from PIL import Image
# from dotenv import load_dotenv

# load_dotenv()

# client = AzureOpenAI(
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#     api_version="2024-12-01-preview",
# )

# DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

# def pil_image_to_base64(image: Image.Image) -> str:
#     buffer = io.BytesIO()
#     image.save(buffer, format="PNG")
#     return base64.b64encode(buffer.getvalue()).decode("utf-8")

# SYSTEM_PROMPT = """
# You are an expert in reading medical Purchase Orders (POs).

# Your task:
# - Extract each item row from the page.
# - Map each row to the POItemModel fields.
# - Use the exact text from the PO.
# - Do NOT hallucinate values.
# - If a field is not present, return null.
# - Keep full medicine names and descriptions.

# Return ONLY valid JSON.
# """


# def build_user_prompt(page_number):
#     return f"""
# This is page {page_number} of a medical Purchase Order.

# Extract all item rows and return them as a list of POItemModel objects.

# Important rules:
# - ProductDescription must always be present.
# - ExtendedProductName should only be filled if a longer version exists on the next line.
# - Do NOT repeat ProductDescription in ExtendedProductName.
# - Use exact values from the PO.

# Return format:
# [
#   {{
#     "ProductDescription": "...",
#     "ExtendedProductName": "...",
#     "UnitOfMeasure": "...",
#     "HSNCode": "...",
#     "Quantity": 0,
#     "Price": 0.0,
#     "RCRate": null,
#     "ItemCodeFromPO": "...",
#     "Marked": 1
#   }}
# ]
# """


# def extract_po_items_from_image(image_base64 ,page_number):

#     response = client.chat.completions.parse(
#         model=DEPLOYMENT_NAME,
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": build_user_prompt(page_number)},
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": f"data:image/png;base64,{image_base64}"
#                         }
#                     }
#                 ]
#             }
#         ],
#         response_format=POItemList
#     )

#     return response.choices[0].message.parsed



# def extract_po_items_from_pdf_pages(image_list):

#     all_po_items = []

#     for i, img in enumerate(image_list, start=1):
#         print(f"Processing page {i}...")
#         # 1. Convert PIL image → base64
#         image_base64 = pil_image_to_base64(img)

#         page_items = extract_po_items_from_image(image_base64, i)
#         # all_po_items.extend(page_items)
#         all_po_items.extend(page_items.items)

#     return all_po_items


from pydantic import BaseModel, Field
from openai import AzureOpenAI
from models.po_models import POItemList
from dotenv import load_dotenv
import os

load_dotenv()

# Deployment name (model)
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")


SYSTEM_PROMPT = """
You are an expert in reading medical Purchase Orders (POs).

Your task:
- Extract each item row from the OCR text.
- Map each row to the POItemModel fields.
- Use the exact text from the PO.
- Do NOT hallucinate values.
- If a field is not present, return null.
- Keep full medicine names and descriptions.

Return ONLY valid JSON.
"""


def build_user_prompt(ocr_text):
    """Build user prompt with actual OCR text"""
    return f"""
This is the OCR text of a medical Purchase Order:

{ocr_text}

Extract all item rows and return them as a list of POItemModel objects.

Important rules:
- ProductDescription must always be present.
- ExtendedProductName should only be filled if a longer version exists on the next line.
- Do NOT repeat ProductDescription in ExtendedProductName.
- Use exact values from the PO.

Return format:
[
  {{
    "ProductDescription": "...",
    "ExtendedProductName": "...",
    "UnitOfMeasure": "...",
    "HSNCode": "...",
    "Quantity": 0,
    "Price": 0.0,
    "RCRate": null,
    "ItemCodeFromPO": "...",
    "Marked": 1
  }}
]
"""

def extract_po_items_from_pdf_pages(ocr_text):

    response = client.chat.completions.parse(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(ocr_text)
            }
        ],
        response_format=POItemList
    )

    return response.choices[0].message.parsed 
 