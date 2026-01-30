# def get_table_x_bounds(table):
#     all_X=[]
#     for cell in table.cells:
#         for regions in cell.bounding_regions:
#             all_X.extend(regions.polygon[0::2])
#     return min(all_X),max(all_X)

def get_table_x_bounds(table: dict):
    all_x = []

    for cell in table.get("cells", []):
        for region in cell.get("bounding_regions", []):
            polygon = region.get("polygon", [])
            # X coordinates are even indices
            all_x.extend(polygon[0::2])

    if not all_x:
        raise ValueError("No X coordinates found in OCR table")

    return min(all_x), max(all_x)
