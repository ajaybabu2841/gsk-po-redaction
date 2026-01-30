# from utils.logging.logger import get_logger 

# logger = get_logger(__name__)

# def get_y1_y2_from_ocr(ocr_tables, grid_idx, start_row, end_row):

#     logger.info(
#         "ENTER get_y1_y2_from_ocr | table=%d | start_row=%d | end_row=%d",
#         grid_idx,
#         start_row,
#         end_row
#     )

#     table = ocr_tables[grid_idx]["cells"]

#     y1 = None
#     y2 = None

#     for cell in table:
#         row = cell["row_index"]
#         col = cell["column_index"]
#         text = cell.get("content", "")

#         if not cell.get("bounding_regions"):
#             continue

#         poly = cell["bounding_regions"][0]["polygon"]

#         if row == start_row:
#             cell_y1 = min(poly[1], poly[3], poly[5], poly[7])
#             logger.info(
#                 "Y1 SOURCE | row=%d col=%d | y=%.4f | text=%r | poly=%s",
#                 row, col, cell_y1, text, poly
#             )
#             y1 = cell_y1

#         if row == end_row:
#             cell_y2 = max(poly[1], poly[3], poly[5], poly[7])
#             logger.info(
#                 "Y2 SOURCE | row=%d col=%d | y=%.4f | text=%r | poly=%s",
#                 row, col, cell_y2, text, poly
#             )
#             y2 = cell_y2

#     logger.info(
#         "EXIT get_y1_y2_from_ocr | table=%d | y1=%.4f | y2=%.4f",
#         grid_idx,
#         y1 if y1 is not None else -1,
#         y2 if y2 is not None else -1
#     )

#     return y1, y2

from utils.logging.logger import get_logger 

logger = get_logger(__name__)

def get_y1_y2_from_ocr(ocr_tables, grid_idx, start_row, end_row):

    logger.info(
        "ENTER get_y1_y2_from_ocr | table=%d | start_row=%d | end_row=%d",
        grid_idx,
        start_row,
        end_row
    )

    table = ocr_tables[grid_idx]["cells"]

    y1_candidates = []
    y2_candidates = []

    for cell in table:
        row = cell["row_index"]
        col = cell["column_index"]
        text = cell.get("content", "")

        if not cell.get("bounding_regions"):
            continue

        poly = cell["bounding_regions"][0]["polygon"]

        cell_min_y = min(poly[1], poly[3], poly[5], poly[7])
        cell_max_y = max(poly[1], poly[3], poly[5], poly[7])

        if row == start_row:
            logger.info(
                "Y1 SOURCE | row=%d col=%d | y=%.4f | text=%r | poly=%s",
                row, col, cell_min_y, text, poly
            )
            y1_candidates.append(cell_min_y)

        if row == end_row:
            logger.info(
                "Y2 SOURCE | row=%d col=%d | y=%.4f | text=%r | poly=%s",
                row, col, cell_max_y, text, poly
            )
            y2_candidates.append(cell_max_y)

    y1 = min(y1_candidates) if y1_candidates else None
    y2 = max(y2_candidates) if y2_candidates else None

    logger.info(
        "EXIT get_y1_y2_from_ocr | table=%d | y1=%.4f | y2=%.4f",
        grid_idx,
        y1 if y1 is not None else -1,
        y2 if y2 is not None else -1
    )

    return y1, y2
