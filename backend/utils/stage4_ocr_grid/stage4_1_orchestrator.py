from utils.stage4_ocr_grid.stage4_2_grid_conversion import convert_table_to_grid
from utils.stage4_ocr_grid.stage4_3_grid_to_md import convert_grid_to_markdown
from utils.stage4_ocr_grid.stage4_4_recognize_po_table import recognize_po_table
from models.po_models import POTableEvaluation, POTableEvaluationResult
from utils.stage4_ocr_grid.stage4_0_extract_page_num import extract_page_number_from_table
from tabulate import tabulate
from utils.stage4_ocr_grid.header_detection import detect_header_rows
from utils.logging.logger import get_logger

logger = get_logger(__name__)

def debug_table_card(table):
    print("\n" + "═" * 90)
    print(f"📄 TABLE INDEX : {table.table_index}")
    print(f"📄 PAGE        : {table.page_number}")
 
    status = "✅ PO TABLE" if table.is_po else "❌ NOT PO"
    print(f"🔍 STATUS      : {status}")
 
    if table.med_col_idx is not None:
        print(f"💊 MED COL IDX : {table.med_col_idx}")
 
    print(f"🧠 LLM REASON  : {table.reason}")
    print("═" * 90)
 
    headers = table.grid[0]
    rows = table.grid[1:]
 
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
    print("═" * 90)
 
 
  
def evaluate_tables_for_po(tables):
    """
    tables: List of OCR-extracted table objects.
            Each table is assumed to already contain page_number metadata.
    """

    results = []

    for index, table in enumerate(tables):

        # 1. Extract page number from OCR table
        page_number = extract_page_number_from_table(table)

        # 2. Convert table → grid
        grid = convert_table_to_grid(table)

        # 3. Convert grid → markdown
        markdown = convert_grid_to_markdown(grid)

        # 4. Call LLM to determine if PO table

        # is_po,reason = recognize_po_table(markdown)
        result = recognize_po_table(markdown)
        is_po = result.get("is_po", False)
        reason = result.get("reason", "")
        med_col_idx = result.get("med_col_idx")

        if is_po:
            header_rows = detect_header_rows(grid)
        else:
            header_rows = None

        logger.info("Detected header rows: %s", header_rows)

        # 5. Store result in Pydantic model
        table_result = POTableEvaluation(
            table_index=index,
            page_number=page_number,
            grid=grid,
            markdown=markdown,
            is_po=is_po, 
            reason=reason,
            med_col_idx=med_col_idx,
            header_rows = header_rows
        )

        # 6. Append to results
        # debug_table_card(table_result)
        results.append(table_result)

    return POTableEvaluationResult(tables=results)
 