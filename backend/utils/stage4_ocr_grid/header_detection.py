def detect_header_rows(grid: list[list[str]]) -> list[int]:
    """
    Detect header rows in a PO table grid using deterministic rules.

    Args:
        grid: 2D list of strings representing OCR table grid

    Returns:
        List of row indices that are header rows
    """

    HEADER_KEYWORDS = {
        "sl", "sno", "sr",
        "item", "product", "description",
        "qty", "quantity", "pack",
        "uom", "unit",
        "rate", "price", "mrp",
        "tax", "gst", "cgst", "sgst",
        "hsn",
        "discount", "amount", "value"
    }

    def tokenize(text: str) -> list[str]:
        text = text.lower()
        text = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text)
        return [t for t in text.split() if t]

    def is_value_token(token: str) -> bool:
        return any(ch.isdigit() for ch in token) or "%" in token

    header_rows = []

    if not grid:
        return header_rows

    rows_to_check = min(len(grid), 4)

    for row_index in range(rows_to_check):
        row = grid[row_index]

        # Collect non-empty cells
        row_texts = [cell.strip() for cell in row if cell and cell.strip()]
        if not row_texts:
            continue

        # Tokenize
        tokens = []
        for text in row_texts:
            tokens.extend(tokenize(text))
        if not tokens:
            continue

        # Count signals
        token_count = len(tokens)
        header_hits = 0
        value_hits = 0

        for token in tokens:
            if token in HEADER_KEYWORDS:
                header_hits += 1
            if is_value_token(token):
                value_hits += 1

        # Reject value-containing rows
        if value_hits > 0:
            continue

        # Strong header rule
        if header_hits >= 2:
            header_rows.append(row_index)
            continue

        # Short header rule (e.g. "Sl Item Qty")
        if token_count <= 3 and header_hits == token_count:
            header_rows.append(row_index)
            continue

    return header_rows
 