
 

# from typing import List, Set, Tuple, Optional
# import re

# def find_non_gsk_row_span(
#     po_grid: List[List[str]],
#     ocr_table: dict,
#     med_col_idx: int,
#     grid_idx: int,
#     non_gsk_med_list: List[str],   # ORDERED, SEQUENTIAL
# ) -> Tuple[int, Optional[int], Optional[int]]:

#     row_count = ocr_table["row_count"]
#     col_count = ocr_table["column_count"]

#     # -----------------------------
#     # Normalization
#     # -----------------------------
#     def normalize(text: str) -> str:
#         text = re.sub(r"hsn\s*:\s*\d+", "", text, flags=re.IGNORECASE)
#         text = re.sub(r"[^a-zA-Z0-9]", "", text)
#         return text.lower()

#     normalized_non_gsk = [normalize(m) for m in non_gsk_med_list]

#     start_row: Optional[int] = None
#     end_row: Optional[int] = None

#     # ============================================================
#     # OUTER LOOP → NON-GSK MEDICINES (SEQUENTIAL)
#     # ============================================================
#     for nongsk in normalized_non_gsk:

#         r = 0
#         while r < row_count:

#             row = po_grid[r]

#             if med_col_idx >= len(row):
#                 r += 1
#                 continue

#             cell = row[med_col_idx].strip() if row[med_col_idx] else ""
#             if not cell:
#                 r += 1
#                 continue

#             # ------------------------------------------------
#             # MATCH ATTEMPTS (STRICT ORDER)
#             # ------------------------------------------------
#             match_found = False
#             matched_coords: Set[Tuple[int, int]] = set()

#             best_candidate = {
#                 "coords": None,
#                 "score": 0.0
#             }

#             # ---------- (r, c)
#             cand = normalize(cell)
#             ok, score = match(cand, nongsk)

#             if ok:
#                 matched_coords = {(r, med_col_idx)}
#                 match_found = True
#             elif score >= 0.1 and score > best_candidate["score"]:
#                 best_candidate = {
#                     "coords": {(r, med_col_idx)},
#                     "score": score
#                 }

#             # ---------- (r, c) + (r+1, c)
#             if not match_found and r + 1 < row_count:
#                 below = po_grid[r + 1][med_col_idx].strip()
#                 if below:
#                     cand = normalize(cell + below)
#                     ok, score = match(cand, nongsk)

#                     if ok:
#                         matched_coords = {(r, med_col_idx), (r + 1, med_col_idx)}
#                         match_found = True
#                     elif score >= 0.1 and score > best_candidate["score"]:
#                         best_candidate = {
#                             "coords": {(r, med_col_idx), (r + 1, med_col_idx)},
#                             "score": score
#                         }

#             # ---------- (r, c-1) + (r, c)
#             if not match_found and med_col_idx - 1 >= 0:
#                 left = row[med_col_idx - 1].strip()
#                 if left:
#                     cand = normalize(left + cell)
#                     ok, score = match(cand, nongsk)

#                     if ok:
#                         matched_coords = {(r, med_col_idx - 1), (r, med_col_idx)}
#                         match_found = True
#                     elif score >= 0.1 and score > best_candidate["score"]:
#                         best_candidate = {
#                             "coords": {(r, med_col_idx - 1), (r, med_col_idx)},
#                             "score": score
#                         }

#             # ---------- (r, c-1) + (r, c) + (r, c+1)
#             if (
#                 not match_found
#                 and med_col_idx - 1 >= 0
#                 and med_col_idx + 1 < col_count
#             ):
#                 left = row[med_col_idx - 1].strip()
#                 right = row[med_col_idx + 1].strip()

#                 if left and right:
#                     cand = normalize(left + cell + right)
#                     ok, score = match(cand, nongsk)

#                     if ok:
#                         matched_coords = {
#                             (r, med_col_idx - 1),
#                             (r, med_col_idx),
#                             (r, med_col_idx + 1)
#                         }
#                         match_found = True
#                     elif score >= 0.1 and score > best_candidate["score"]:
#                         best_candidate = {
#                             "coords": {
#                                 (r, med_col_idx - 1),
#                                 (r, med_col_idx),
#                                 (r, med_col_idx + 1)
#                             },
#                             "score": score
#                         }

#             # ------------------------------------------------
#             # MATCH RESOLUTION
#             # ------------------------------------------------
#             if match_found:
#                 final_coords = matched_coords

#             elif best_candidate["coords"] is not None:
#                 final_coords = best_candidate["coords"]
#                 # logger.warning(
#                 #     "MANUAL REQUIRED | table=%d | row=%d | confidence=%.2f",
#                 #     grid_idx,
#                 #     r,
#                 #     best_candidate["score"]
#                 # )
#                 print(
#                     f"MANUAL REQUIRED | table={grid_idx} | row={r} | confidence={best_candidate['score']:.2f}"
#                 )


#             else:
#                 r += 1
#                 continue

#             rows = {rr for rr, _ in final_coords}
#             curr_start = min(rows)
#             curr_end = max(rows)

#             if start_row is None:
#                 start_row = curr_start
#             end_row = curr_end

#             r = curr_end + 1   # ROW SKIP
#             break              # NEXT NON-GSK MED

#     return grid_idx, start_row, end_row

from rapidfuzz import fuzz
# 
from typing import List, Set, Tuple
import re

def log_match_attempt(
    grid_idx: int,
    row: int,
    scenario: str,
    candidate: str,
    target: str,
    ok: bool,
    score: float,
):
    print(
        f"MATCH_ATTEMPT | table={grid_idx} | row={row} | scenario={scenario} | "
        f"candidate='{candidate}' | target='{target}' | "
        f"score={score:.3f} | ok={ok}"
    )


def match(candidate: str, target: str) -> tuple[bool, float]:
    score = min(
        fuzz.ratio(candidate, target),
        fuzz.partial_ratio(candidate, target), # Don't use it
        fuzz.token_sort_ratio(candidate, target) 
    ) / 100.0  # normalize to 0–1

    return score >= 0.90, score

def normalize(text: str) -> str:
    return re.sub(
        r'(?i)\bhsn(?:\s*code)?\s*:?\s*\d+\b',
        '',
        text
    ).strip().lower()

def find_non_gsk_row_spans(
    po_grid: List[List[str]],
    ocr_table: dict,
    med_col_idx: int,
    grid_idx: int,
    non_gsk_med_list: List[str],   # ORDERED
) -> List[Tuple[int, int]]:

    row_count = ocr_table["row_count"]
    col_count = ocr_table["column_count"]

    # -----------------------------
    # Normalization
    # -----------------------------

    normalized_non_gsk = [normalize(m) for m in non_gsk_med_list]
    print( normalized_non_gsk)

    spans: List[Tuple[int, int]] = []

    # -------------------------------------------------
    # SINGLE forward row pointer (CRITICAL FIX)
    # -------------------------------------------------
    r = 0

    for nongsk in normalized_non_gsk:

        while r < row_count:

            row = po_grid[r]

            # NOTE: does not make sense
            if med_col_idx >= len(row):
                raise Exception("Predicted medicine column index is less than the number of columns found in table (grid)")
                # r += 1
                # continue

            cell = row[med_col_idx].strip() if row[med_col_idx] else ""
            if not cell:
                r += 1
                continue

            best_candidate = {
                "coords": None,
                "score": 0.0
            }

            match_found = False
            final_coords: Set[Tuple[int, int]] = set()

            # =================================================
            # (r, c)
            # =================================================
            cand = normalize(cell)
            ok, score = match(cand, nongsk)

            log_match_attempt(
                grid_idx,
                r,
                "(r,c)",
                cand,
                nongsk,
                ok,
                score
            )

            if ok:
                final_coords = {(r, med_col_idx)}
                match_found = True
            elif score >= 0.4:
                best_candidate = {
                    "coords": {(r, med_col_idx)},
                    "score": score
                }

            print( "score" , {score})

            # =================================================
            # (r, c) + (r+1, c)
            # =================================================
            if not match_found and r + 1 < row_count:
                below = po_grid[r + 1][med_col_idx].strip()
                if below:
                    # cand = normalize(cell + below)
                    # ok, score = match(cand, nongsk)

                    cand = normalize(cell + below)
                    ok, score = match(cand, nongsk)

                    log_match_attempt(
                        grid_idx,
                        r,
                        "(r,c)+(r+1,c)",
                        cand,
                        nongsk,
                        ok,
                        score
                    )


                    if ok:
                        final_coords = {(r, med_col_idx), (r + 1, med_col_idx)}
                        match_found = True
                    elif score >= 0.4 and score > best_candidate["score"]:
                        best_candidate = {
                            "coords": {(r, med_col_idx), (r + 1, med_col_idx)},
                            "score": score
                        }
                    print( "score" , {score})

            # =================================================
            # (r, c-1) + (r, c)
            # =================================================
            if not match_found and med_col_idx - 1 >= 0:
                left = row[med_col_idx - 1].strip()
                if left:
                    # cand = normalize(left + cell)
                    # ok, score = match(cand, nongsk)
                    cand = normalize(left + cell)
                    ok, score = match(cand, nongsk)

                    log_match_attempt(
                        grid_idx,
                        r,
                        "(r,c-1)+(r,c)",
                        cand,
                        nongsk,
                        ok,
                        score
                    )


                    if ok:
                        final_coords = {(r, med_col_idx - 1), (r, med_col_idx)}
                        match_found = True
                    elif score >= 0.4 and score > best_candidate["score"]:
                        best_candidate = {
                            "coords": {(r, med_col_idx - 1), (r, med_col_idx)},
                            "score": score
                        }
                    print( "score" , {score})

            # =================================================
            # (r, c-1) + (r, c) + (r, c+1)
            # =================================================
            if (
                not match_found
                and med_col_idx - 1 >= 0
                and med_col_idx + 1 < col_count
            ):
                left = row[med_col_idx - 1].strip()
                right = row[med_col_idx + 1].strip()

                if left and right:
                    # cand = normalize(left + cell + right)
                    # ok, score = match(cand, nongsk)
                    

                    if ok:
                        final_coords = {
                            (r, med_col_idx - 1),
                            (r, med_col_idx),
                            (r, med_col_idx + 1),
                        }
                        match_found = True
                    elif score >= 0.4 and score > best_candidate["score"]:
                        best_candidate = {
                            "coords": {
                                (r, med_col_idx - 1),
                                (r, med_col_idx),
                                (r, med_col_idx + 1),
                            },
                            "score": score
                        }
                    print( "score" , {score})

            # =================================================
            # RESOLUTION
            # =================================================
            if not match_found and best_candidate["coords"]:
                final_coords = best_candidate["coords"]
                print(
                    f"MANUAL REQUIRED | table={grid_idx} | row={r} | confidence={best_candidate['score']:.2f}"
                )

            if final_coords:
                rows = {rr for rr, _ in final_coords}
                start = min(rows)
                end = max(rows)

                spans.append((start, end))

                r = end + 1     # 🔴 definitive forward skip
                break           # move to next non-GSK medicine

            else:
                r += 1

    return spans