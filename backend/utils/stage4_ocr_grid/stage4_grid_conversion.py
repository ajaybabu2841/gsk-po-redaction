def display_table_robust(table_data, render=True):
    try:
        all_cells = []
        for row in table_data:
            if isinstance(row, list):
                all_cells.extend(row)
            else:
                all_cells.append(row)

        if not all_cells:
            return [], ""

        max_row = max(cell.get("row_index", 0) for cell in all_cells)
        max_col = max(cell.get("col_index", 0) for cell in all_cells)

        grid = [['' for _ in range(max_col + 1)] for _ in range(max_row + 1)]

        for cell in all_cells:
            r = cell.get("row_index", 0)
            c = cell.get("col_index", 0)
            text = str(cell.get("text", "")).strip()
            grid[r][c] = text if text else " "

        md_lines = []
        md_lines.append("| " + " | ".join(grid[0]) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(grid[0])) + " |")
        for row in grid[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        md = "\n".join(md_lines)

        return grid

    except Exception as e:
        import traceback
        traceback.print_exc()
        return [], ""


def adi_table_to_display_cells(po_table: dict):
    cells = []
    for cell in po_table.get("cells", []):
        cells.append({
            "row_index": cell.get("row_index", 0),
            "col_index": cell.get("column_index", 0),
            "text": (cell.get("content") or "").strip(),
        })
    return cells


def build_grids_from_tables(po_tables):
    grids = []
    for po_table in po_tables:
        display_cells = adi_table_to_display_cells(po_table)
        grid, _ = display_table_robust(display_cells)
        grids.append(grid)
    return grids