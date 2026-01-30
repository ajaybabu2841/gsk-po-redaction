import json
from typing import List
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from openai import AzureOpenAI
from dotenv import load_dotenv
from models.po_models import PoClassifyModel
import os
from collections import defaultdict
from utils.stage0.pdf_bytes_to_image import pdf_bytes_to_images
# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
)

# Deployment name (model)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

########################### Added ############################

def pil_image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def classify_po_page_image(
    image_base64: str,
    client: AzureOpenAI,
) -> PoClassifyModel:

    response = client.chat.completions.parse(
        model=DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": PO_CLASSIFY_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this PO page image and classify it.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        },
                    },
                ],
            },
        ],
        temperature=0.1,
        max_tokens=512,
        response_format=PoClassifyModel,
    )

    return response.choices[0].message.parsed


PO_CLASSIFY_SYSTEM_PROMPT = """
You are a professional PDF structural quality analyzer specializing in Purchase Order (PO) tables.

You will be given content extracted from PDF bytes (via OCR or text extraction).
Your task is to classify the PDF into **exactly ONE** of the following categories based on the dominant structural issue observed.

### Allowed Classification Labels (choose exactly one):

* Bad Quality
* OverCrowded
* Header & Row Items are multiline
* Row Items are multiline but not Header
* Row Items are Misaligned to the Header

You must not invent new labels.

---

## Classification Rules (Strict)

* Always return **one and only one** classification label.
* If multiple issues exist, select the **most dominant structural problem**.
* If text quality is poor or unreliable, always choose **Bad Quality**, regardless of other issues.
* Do not provide explanations unless explicitly asked.
* Base the decision only on structural layout and readability, not business meaning.

---

## Category Definitions with Examples

### Bad Quality

Classify as **Bad Quality** if any of the following are true:

* Document is scanned or photocopied
* Text is blurred, faded, distorted, or unreadable
* OCR output is highly inaccurate or inconsistent
* Handwritten text is present
* Table structure cannot be reliably identified

No example provided. Prioritize this label whenever text quality itself is unreliable.

---

### OverCrowded

Choose **OverCrowded** when:

* Columns are extremely close together
* Text appears visually compressed or overlapping
* Spacing between values is insufficient to distinguish columns
* A single row contains too many densely packed fields

Example:

| SNO | Group       Item Name                         Qty  UOM   Rate  UMRP  Tax   Total MRP  HSN       SP    Value  Disc % Disc Amt  Disc Value Tax % Tax Free UOM |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | TABLETS    ULTRA OMEGA-3[MEYER] CAP (10 cap)  200  EACH 15.63 26.20  0.74   5240.00   30049099 24.95  3126.00 5      156.30  2969.70     5   148.49  EACH   |

```
     & CAPSULES
```

---

### Header & Row Items are multiline

Choose **Header & Row Items are multiline** when:

* Header labels span multiple lines or rows
* A single logical header is split across rows
* Item rows are also multiline
* Both header and row sections are structurally multiline

Example:
| Sl. No | Order No.   | Item Name                                   | Qty   | Tax % | Unit Rate (Rs.) | MRP (Rs.) | Total Value (Rs.) |
|--------|-------------|---------------------------------------------|pk Type|-------|-----------------|-----------|-------------------|
| 1      | 64790018435 | BETNOVATE GM CREAM (20GM) [I08254]           | 30    | 5.00  | 24.60           | 46.63     | 774.90            |
|        |             | [glaxo Smithkline Pharmaceuticals Ltd]      |1X1 TUBE|       |                 |           |                   |

---

### Row Items are multiline but not Header

Choose **Row Items are multiline but not Header** when:

* Header row is single-line and properly aligned
* Item descriptions or values continue on subsequent lines
* Continuation lines belong to the same logical row
* Column alignment is otherwise preserved

Example:

| Sl. No | Order No.   | Item Name                              | Qty | Tax % | Unit Rate (Rs.) | MRP (Rs.) | Total Value (Rs.) |
| ------ | ----------- | -------------------------------------- | --- | ----- | --------------- | --------- | ----------------- |
| 1      | 64790018435 | BETNOVATE GM CREAM (20GM) [I08254]     | 30  | 5.00  | 24.60           | 46.63     | 774.90            |
|        |             | [glaxo Smithkline Pharmaceuticals Ltd] |     |       |                 |           |                   |

---

### Row Items are Misaligned to the Header

Choose **Row Items are Misaligned to the Header** when:

* Header row is clean and well-structured
* Item row values spill into adjacent columns
* Item-related text appears below or outside the table grid
* Column-to-value mapping is inconsistent or broken

Example:

| SNO | ITEM       | QTY/FR | UOM   | GROSS PRICE | DISC. | NET PRICE | AMOUNT   | TAX %               |
| --- | ---------- | ------ | ----- | ----------- | ----- | --------- | -------- | ------------------- |
| 10  | 1000006241 | 10     | STRIP | 228.81      | 4 %   | 219.66    | 2,196.58 | SGST@2.50 CGST@2.50 |

```
HSN Code:30049082
ACITROM 1 MG TAB
ACITROM 1 MG TABLET
```

---

## Confidence Scoring

Return a confidence score between **0.0 and 1.0** based on how strongly the document matches the chosen category.

* **0.90 – 1.00** → Very clear, unambiguous match
* **0.70 – 0.89** → Clear match with minor ambiguity
* **0.50 – 0.69** → Moderate ambiguity
* **Below 0.50** → Weak or unclear match (use only if unavoidable)

Confidence reflects **structural certainty**, not general confidence.

---

## Output Requirement

Return:

* `type`: one exact label from the allowed list
* `confidence`: a float between 0.0 and 1.0

Do not include explanations or additional text.

"""


def classify_po_pdf_from_images(pdf_bytes: bytes) -> PoClassifyModel:
    images = pdf_bytes_to_images(pdf_bytes)

    page_results: list[PoClassifyModel] = []

    # for img in images:
    #     result = classify_po_page_image(img, client)
    #     page_results.append(result)

    for img in images:
        img_base64 = pil_image_to_base64(img)
        result = classify_po_page_image(img_base64, client)
        page_results.append(result)


    # Pick the classification with highest confidence
    final = max(page_results, key=lambda x: x.Confidence)
    return final