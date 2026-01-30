from typing import List
import io, base64 # PyMuPDF
from PIL import Image
from openai import AzureOpenAI
from dotenv import load_dotenv
from models.po_models import MedicineList
from utils.stage0.pdf_bytes_to_image import pdf_bytes_to_images
import os

# -------------------------------------------------
# Azure OpenAI Client
# -------------------------------------------------

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

def pil_image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# -------------------------------------------------
# Prompt
# -------------------------------------------------

GENERIC_PO_PROMPT = """
You need to go through the provided purchase order page image
and extract all item  names present on that page.

Rules:
- Return all the item names exactly as they appear. NOTE: DON'T CHANGE ANY THING
- Do NOT hallucinate or normalize names. EVEN IF THERE IS A SPELLING MISTAKE PLEASE KEEP IT AS IT IS
- Write the names as it is without any adulteration.
- Include duplicates if they appear on the page.
- Return an empty list if no items are found.

- IMPORTANT NOTE : In some cases for a particular row the place where the item name is mentioned there might other information present in the same cell below the item name which is actually together. So please take everything that is present there and not just the item name.

Few Examples mentioned here are: 

1.      SUPACEF 1.5GM (INJ)
        Manuf: Glaxo SmithKline
        Pharmaceuticals Ltd
        HSN: 30042019
        Chemical Name: Cefuroxime sodium
        1500 MG
    
    -> Here everything should be taken and not just the "SUPACEF 1.5GM (INJ)"

2.      T-BACT - 1*5GM ONT.
        CGST
        SGST

    -> Here everything is need to be taken not just "T-BACT - 1*5GM ONT."

- These are just examples of the numerous cases that might come across so we will have to take the entire information that is seemingly present in the single cell of a single row.
 
"""

MANIPAL_PO_PROMPT = """
You need to go through the provided purchase order page image
and extract all item  names present on that page.

Rules:
- This is Manipal PO and in this PO we have repitative item names right after another, often one smaller version and anothe longer version. Both names don't align with the column demactaion, keep in mind to extract both word to word even if it feels redundant 
- Return all the item names exactly as they appear. NOTE: DON'T CHANGE ANY THING
- Do NOT hallucinate or normalize names. EVEN IF THERE IS A SPELLING MISTAKE PLEASE KEEP IT AS IT IS
- Write the names as it is without any adulteration.
- Include duplicates if they appear on the page
- Return an empty list if no items are found

- Giving an example of the MANIPAL po here such that both are taken

        10 1000025164 15 Bottle 280.29 4 % 269.08 4,036.18 SGST@2.50 
                                                        CGST@2.50
            HSN Code:30045090
            CCM TABLET (40S), GSK
        CCM TABLET (40S) (CALCIUM CITRATE MALATE 250 MG+VITAMIN D3 100 IU+FOLIC ACID 50 MCG), GSK

    -> Here both the : "CCM TABLET (40S), GSK" and the "CCM TABLET (40S) (CALCIUM CITRATE MALATE 250 MG+VITAMIN D3 100 IU+FOLIC ACID 50 MCG), GSK" needs to be extracted.
"""


# -------------------------------------------------
# Extract Medicines From ONE Page Image
# -------------------------------------------------

def extract_medicines_from_page_image(
    image_base64: str,
    is_manipal=True
) -> MedicineList:
    if is_manipal:
        prompt = MANIPAL_PO_PROMPT
    else:
        prompt = GENERIC_PO_PROMPT
    response = client.chat.completions.parse(
        model=DEPLOYMENT_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        },
                    },
                ],
            }
        ],
        temperature=0.1,
        max_tokens=1000,
        response_format=MedicineList,
    )

    return response.choices[0].message.parsed


# -------------------------------------------------
# Extract Medicines From ALL Pages (PDF-Level)
# -------------------------------------------------

def extract_all_medicines_from_images(image_list):
    all_meds = []

    for img in image_list:
        img_base64 = pil_image_to_base64(img)
        page_result = extract_medicines_from_page_image(img_base64)
        # page_result = extract_medicines_from_page_image(img)

        if page_result and page_result.MedicineListName:
            all_meds.extend(page_result.MedicineListName)

    print("$")
    print(" medicines from LLM")
    for med in all_meds:
        print(med)
    print("$")
    return all_meds
