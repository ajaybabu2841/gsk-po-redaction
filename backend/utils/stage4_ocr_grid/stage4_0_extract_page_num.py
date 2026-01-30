def extract_page_number_from_table(table: dict) -> int | None:
    for cell in table.get("cells", []):
        for region in cell.get("bounding_regions", []):
            if "page_number" in region:
                return region["page_number"]
    return None