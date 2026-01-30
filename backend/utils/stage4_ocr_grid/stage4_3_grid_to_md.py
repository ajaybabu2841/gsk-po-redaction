def convert_grid_to_markdown(grid):
    """
    Converts a 2D grid (list of lists) into raw Markdown.
    No header assumptions. No normalization. No interpretation.
    """

    if not grid:
        return ""

    md_lines = []

    num_cols = max(len(row) for row in grid)

    # Add all rows exactly as they are
    for row in grid:
        row_cells = [
            str(cell) if cell is not None else ""
            for cell in row + [""] * (num_cols - len(row))
        ]
        md_lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(md_lines)

 