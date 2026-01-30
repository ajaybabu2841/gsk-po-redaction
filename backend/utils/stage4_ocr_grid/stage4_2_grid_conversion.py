def convert_table_to_grid(table: dict):
    """
    Converts a single OCR-extracted table into a 2D grid.
    No normalization. No markdown. No LLM logic.
    """

    # Step 1: Extract display cells from OCR table
    cells = adi_table_to_display_cells(table)

    # Step 2: Build grid from row/column indices
    grid = build_grid_from_cells(cells)

    return grid



def adi_table_to_display_cells(table: dict):
    return [
        {
            "row_index": cell.get("row_index", 0),
            "col_index": cell.get("column_index", 0),
            "text": cell.get("content", "").strip(),
        }
        for cell in table.get("cells", [])
    ]



def build_grid_from_cells(cells):
    if not cells:
        return []

    max_row = max(c["row_index"] for c in cells)
    max_col = max(c["col_index"] for c in cells)

    grid = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]

    for c in cells:
        r, col = c["row_index"], c["col_index"]
        text = c["text"]

        if grid[r][col]:
            grid[r][col] += " " + text
        else:
            grid[r][col] = text

    return grid
