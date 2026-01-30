#recognize_po_table_llm.py
from openai import AzureOpenAI
from dotenv import load_dotenv
import os , json
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
)

# Deployment name (model)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

# def extract_json_from_llm(content: str):
#     """
#     Safely extract JSON object from LLM text response.
#     Works even if LLM adds explanations or extra text.
#     """
#     try:
#         match = re.search(r"\{[\s\S]*\}", content)
#         if not match:
#             raise ValueError("No JSON object found in LLM response")
#         return json.loads(match.group())
#     except Exception:
#         return {
#             "is_po": False,
#             "reason": "LLM returned invalid JSON",
#             "med_col_idx": None
#         }
 
from pydantic import BaseModel, Field
class IsPOData(BaseModel):
    is_po: bool = Field(description="")
    reason: str = Field(description="Reason why hsi table is PO or not PO")
    med_col_idx: int = Field(description="Index of the column where the medicine name is present")

def recognize_po_table(markdown):
    """
    Analyze a markdown table to determine if it is a Purchase Order (PO) table using LLM.
    
    Args:
        markdown_table: Table in markdown format.
        
    Returns:
        POTableResult: Object containing is_po, column_name_of_item_name, and confidence_score.
    """

    # -----------------------------
    # 🔹 System Prompt
    # -----------------------------
    system_prompt = """
        You are an expert procurement and purchasing assistant specialized in analyzing Purchase Order (PO) tables.
        Your task is to accurately identify PO tables by analyzing both column names AND their corresponding values.

        ----------------------------------------------
        🔹 Fuzzy Header Matching (Important)
        ----------------------------------------------
        Because PDF extraction and OCR often corrupt column names,
        you must apply fuzzy matching to interpret misspelled or partially broken headers.

        Examples of acceptable fuzzy matches:
        - "ItemName" ≈ "ItiemName" ≈ "Item Nm" ≈ "ItmName" ≈ "Description"
        - "Qty" ≈ "QTY" ≈ "Qtiy" ≈ "Quant" ≈ "F.Qty"
        - "UOM" ≈ "UoM" ≈ "U.M"
        - "Price" ≈ "Prce" ≈ "UnitPrice" ≈ "Rate"
        - "TotalPrice" ≈ "TotlPrice" ≈ "TotPrice" ≈ "Amount"

        If column names are unclear but the VALUES clearly represent:
        - product names  
        - numeric quantities  
        - numeric prices  
        - totals  
        then classify it as a PO table but mark "needs_human_review": true.

        ----------------------------------------------
        🔹 Valid PO Table Rules
        ----------------------------------------------
        For a table to be considered a valid PO table:
        1. Column names should indicate a purchasing context (Item, Description, Quantity, UOM, Price, Amount)
        — fuzzy-matching is allowed.
        2. The values in these columns must be logically consistent:
        - Quantity values should be numeric and reasonable
        - Price/Amount values should be valid currency amounts
        - Item descriptions should be real product/service names
        - Tax columns (CGST/SGST/IGST) must contain valid % or amounts
        3. The table data must form a coherent purchase record.

        ----------------------------------------------
        🔹 Non-Commercial / Quantity-Only PO Tables (Important)
        ----------------------------------------------
        In pharmaceutical, hospital, and distributor workflows, many valid Purchase Orders
        DO NOT contain pricing, amount, or tax columns.

        These tables are still valid PO tables if:
        1. The table contains a list of medicines or pharmaceutical products
        2. Each row represents a purchasable item
        3. There is a clear quantity per item
        4. A unit of measure is present or implied (e.g., TAB, INJ, ML, NOS, STRIP)

        Such tables are commonly used for:
        - Drug supply orders
        - Hospital procurement
        - Government tenders
        - Distributor indents

        If a table contains:
        - Medicine/product names
        - Numeric quantities
        - Units (explicit or implicit)

        Then:
        → is_po = true  
        → needs_human_review = false (unless data is corrupted)  

        ----------------------------------------------
        🔹 Reject the table if:
        ----------------------------------------------
        - Values do not match column types when such columns are present
        - Data appears corrupted or misaligned in a way that breaks coherence
        - Content is clearly not purchase-related even if some column names resemble PO columns
        - Both column names AND values do not show PO-like structure

        ----------------------------------------------
        🔹 Medical / Pharmaceutical Signal Boost
        ----------------------------------------------
        If item descriptions contain pharmaceutical indicators such as:
        - Medicine names
        - Dosage patterns (e.g., 500MG, 1.2G, 5%)
        - Forms (TAB, INJ, SYP, GEL, SOAP, DROPS)

        This is a strong indicator of a Purchase Order even if pricing information is missing.

        ----------------------------------------------
        🔹 Ambiguous Case Handling
        ----------------------------------------------
        If column names are corrupted but values strongly indicate a PO (product names, numeric qtys, numeric prices):
        → is_po = true  

        If both column names and values are weak/unrelated:
        → is_po = false  

        You must rely on BOTH:
        - fuzzy column interpretation
        - value pattern analysis

          ----------------------------------------------
        🔹 Medicine Column Index Identification
        ----------------------------------------------
        - Go through the markdown and find the column which holds the medicine names/descriptions and return its numeric Index as an Integer

    """

    # -----------------------------
    # 🔹 User Prompt
    # -----------------------------
    user_prompt = f"""
        Analyze the following markdown table and determine if it is a genuine Purchase Order (PO) table.
        Examine both column names AND their corresponding values carefully.
        
        Validation steps:
        1. Check column names for PO indicators:
           - Item/Product description columns
           - Quantity/Units columns
           - Price/Amount columns (Unit price, Total, Discount)
           - Tax related columns (CGST, SGST, etc.)
           - Product/SKU code columns
           - Absence of price or tax columns does NOT invalidate a PO if medicine names and quantities are present
        
        2. Validate the values in each column:
           - Description column: Should contain actual product/service names
           - Quantity column: Should have valid numeric values
           - Price columns: Should contain proper currency amounts
           - Tax columns: Should have valid percentage or amounts
           - All values should be properly aligned with their columns
        
        3. Overall coherence:
           - Data should form a logical purchase record
           - Values across columns should make mathematical sense
           - No obvious data corruption or misalignment
        
        Only mark as PO table if BOTH column names AND values are valid and coherent.
        Return your answer strictly as JSON in this format (no extra text, no explanations):

        {IsPOData.model_json_schema()}
        
        Markdown table:
        {markdown}
    """

 # -----------------------------
    # LLM Call (Structured)
    # -----------------------------
    response = client.chat.completions.parse(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format=IsPOData,
    )

    content = response.choices[0].message.content
    print("*"*50)
    print(content)
    import json
    return json.loads(content)    # return extract_json_from_llm(content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "is_po": False,
            "reason": "LLM returned invalid JSON",
        }
    # -----------------------------
    # Parsed Pydantic Output
    # -----------------------------
    # return response.choices[0].message.parsed

