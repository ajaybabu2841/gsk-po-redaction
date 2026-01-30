# from typing import List, Tuple
# from rapidfuzz import fuzz
# import re

# def match(candidate: str, target: str) -> tuple[bool, float]:
#     return fuzz.token_sort_ratio(normalize(candidate), normalize(target))

# # def normalize(text: str) -> str:
# #     return re.sub(
# #         r'(?i)\bhsn(?:\s*code)?\s*:?\s*\d+\b',
# #         '',
# #         text
# #     ).strip().lower()
# def normalize(text: str) -> str:
#     text = re.sub(
#         r'(?i)\bhsn(?:\s*code)?\s*:?\s*\d+\b',
#         '',
#         text
#     )
#     text = re.sub(r"[,\-_/]", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     return text.strip().lower()


# def is_continuation_row(row):
#     """
#     A continuation row usually has empty HSN and Qty columns
#     meaning it's wrapped text of previous medicine.
#     """
#     try:
#         hsn = row[2].strip()
#         qty = row[3].strip()
#     except IndexError:
#         return False

#     return (hsn == "" or hsn is None) and (qty == "" or qty is None)

# def batch_match(candidate: str, target_list: List[str]):
#     max_score = 0
#     max_index = None
#     for target_index, target in enumerate(target_list):
        
#         score = match(candidate, target)
#         if score >= max_score:
#             max_index = target_index
#             max_score = score

#     return max_score, max_index


# def find_best_combination(
#     combinations: List[Tuple[str, str]], 
#     non_gsk_med_list: List[str]
# ):
#     match_results_for_comb = []    
#     for combination in combinations:
#         max_score, max_index = batch_match(combination[1], non_gsk_med_list)
#         match_results_for_comb.append(
#             (combination[0],
#             max_score,
#             max_index)
#         )

#     match_results_for_comb = sorted(match_results_for_comb, key=lambda x: x[1], reverse=True)
#     return match_results_for_comb[0]

# def find_fragmented_match(
#     po_grid: List[List[str]],
#     med_col_idx: int,
#     non_gsk_med_list: List[str],   # ORDERED
#     header_rows: List[int] | None = None
# ):
#     row_count = len(po_grid)
#     col_count = len(po_grid[0])
#     if header_rows:
#         start_row = max(header_rows) + 1
#     else:
#         start_row = 0

#     row_index = start_row
    
#     rows_to_redact: List[Tuple[int, int]] = []
#     while row_index < row_count:
#         row = po_grid[row_index]

#         # combinations
#         combinations = []
#         combinations.append((1, row[med_col_idx], row_index))
#         if med_col_idx - 1 >= 0:
#             combinations.append((2, row[med_col_idx - 1] + " " + row[med_col_idx], row_index))
#         if med_col_idx - 1 >= 0 and med_col_idx + 1 < col_count:
#             combinations.append((3, row[med_col_idx - 1] + " " + row[med_col_idx] + " " + row[med_col_idx + 1], row_index))

#         if row_index + 1 < row_count:
#             next_row = po_grid[row_index + 1]
#             combinations.append((4, row[med_col_idx] + " " + next_row[med_col_idx], row_index + 1))
    
#         print(f"Checking {row_index}...")
#         combination_index, max_score, non_gsk_index = find_best_combination(combinations, non_gsk_med_list)
#         if max_score < 80:
#             print("Skipping since no best match could be found")
#             if combination_index == 1:
#                 print(f"combination 1 : {row[med_col_idx]} :: {max_score}")
#             elif combination_index == 2:
#                 print(f"combination 2 : {row[med_col_idx - 1] + ' ' + row[med_col_idx]} :: {max_score}")
#             elif combination_index == 3:
#                 print(f"combination 3 : {row[med_col_idx - 1] + ' ' + row[med_col_idx] + ' ' + row[med_col_idx + 1]} :: {max_score}")
#             elif combination_index == 4:
#                 print(f"combination 4 : {row[med_col_idx] + ' ' + next_row[med_col_idx]} :: {max_score}")

#             row_index += 1
#             continue

#         if combination_index == 1:
#             print(f"combination 1 : {row[med_col_idx]} :: {max_score}")
#             rows_to_redact.append((row_index, row_index))
#         elif combination_index == 2:
#             print(f"combination 2 : {row[med_col_idx - 1] + ' ' + row[med_col_idx]} :: {max_score}")
#             rows_to_redact.append((row_index, row_index))
#         elif combination_index == 3:
#             print(f"combination 3 : {row[med_col_idx - 1] + ' ' + row[med_col_idx] + ' ' + row[med_col_idx + 1]} :: {max_score}")
#             rows_to_redact.append((row_index, row_index))
#         elif combination_index == 4:
#             print(f"combination 4 : {row[med_col_idx] + ' ' + next_row[med_col_idx]} :: {max_score}")
#             rows_to_redact.append((row_index, row_index + 1))
        
#         print("non gsk found : ", non_gsk_med_list[non_gsk_index])    
        
#         row_index += 1

#     print( rows_to_redact)

#     return rows_to_redact
from typing import List, Tuple
from rapidfuzz import fuzz
import re


def normalize(text: str) -> str:
    text = re.sub(
        r'(?i)\bhsn(?:\s*code)?\s*:?\s*\d+\b',
        '',
        text
    )
    text = re.sub(r"[,\-_/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

def is_continuation_row(row):
    """
    A continuation row usually has empty HSN and Qty columns
    meaning it's wrapped text of previous medicine.
    """
    try:
        hsn = row[2].strip()
        qty = row[3].strip()
    except IndexError:
        return False

    return (hsn == "" or hsn is None) and (qty == "" or qty is None)


def match(candidate: str, target: str) -> float:
    # return fuzz.token_sort_ratio(normalize(candidate), normalize(target))
    return fuzz.ratio(normalize(candidate), normalize(target))


def batch_match(candidate: str, target_list: List[str]):
    print(f"\n     Candidate being matched: '{candidate}'")
    max_score = 0
    max_index = None

    for target_index, target in enumerate(target_list):
        score = match(candidate, target)

        print(
            f"         Compared with [{target_index}] '{target}' "
            f"=> score = {score}"
        )

        if score >= max_score:
            max_score = score
            max_index = target_index

    print(
        f"    Best match for candidate '{candidate}' "
        f"=> index={max_index}, score={max_score}"
    )

    return max_score, max_index


def find_best_combination(
    combinations: List[Tuple[int, str, int]],
    non_gsk_med_list: List[str]
):
    print("\n   Evaluating combinations for current row")

    match_results_for_comb = []

    for comb_index, comb_text, row_idx in combinations:
        print(
            f"\n  Combination {comb_index} (row ref={row_idx}) "
            f"Text: '{comb_text}'"
        )

        max_score, max_index = batch_match(comb_text, non_gsk_med_list)

        match_results_for_comb.append(
            (comb_index, max_score, max_index, comb_text)
        )

    print("\n   Summary of all combinations:")
    for comb_index, score, idx, text in match_results_for_comb:
        target = non_gsk_med_list[idx] if idx is not None else None
        print(
            f"      Combination {comb_index}: "
            f"score={score}, matched='{target}', text='{text}'"
        )

    match_results_for_comb.sort(key=lambda x: x[1], reverse=True)

    best = match_results_for_comb[0]
    print(
        f"\n   Best combination selected: "
        f"Combination {best[0]} with score {best[1]}"
    )

    return best  # (comb_index, score, non_gsk_index, comb_text)


def find_fragmented_match(
    po_grid: List[List[str]],
    med_col_idx: int,
    non_gsk_med_list: List[str],
    header_rows: List[int] | None = None,
):
    row_count = len(po_grid)
    col_count = len(po_grid[0])
    # row_index = 0

    # ----------------- DETERMINE START ROW -----------------

    if header_rows:
        start_row = max(header_rows) + 1
    else:
        start_row = 0

    row_index = start_row

    rows_to_redact: List[Tuple[int, int]] = []

    while row_index < row_count:
        row = po_grid[row_index]

        print("\n" + "=" * 80)
        print(f" Checking row {row_index}: {row}")

        combinations = []
        combinations.append((1, row[med_col_idx], row_index))

        if med_col_idx - 1 >= 0:
            combinations.append(
                (2, row[med_col_idx - 1] + " " + row[med_col_idx], row_index)
            )

        if med_col_idx - 1 >= 0 and med_col_idx + 1 < col_count:
            combinations.append(
                (
                    3,
                    row[med_col_idx - 1]
                    + " "
                    + row[med_col_idx]
                    + " "
                    + row[med_col_idx + 1],
                    row_index,
                )
            )

        # if row_index + 1 < row_count:
        #     next_row = po_grid[row_index + 1]
            
        #     combinations.append(
        #         (4, row[med_col_idx] + " " + next_row[med_col_idx], row_index + 1)
        #     )
        if row_index + 1 < row_count:
            next_row = po_grid[row_index + 1]
            # added to solve next merging row issue-taking next item name and merging it with current row
            if is_continuation_row(next_row):  
                combinations.append(
                (4, row[med_col_idx] + " " + next_row[med_col_idx], row_index + 1)
            )

        comb_index, max_score, non_gsk_index, comb_text = find_best_combination(
            combinations, non_gsk_med_list
        )

        if max_score < 80:
            print(
                f"\n No valid match found (score={max_score} < 80)"
            )
            row_index += 1
            continue

        print(
            f"\n Match accepted:"
            f"\n   Combination {comb_index}"
            f"\n   Text: '{comb_text}'"
            f"\n   Matched Non-GSK: '{non_gsk_med_list[non_gsk_index]}'"
            f"\n   Score: {max_score}"
        )

        if comb_index == 4:
            rows_to_redact.append((row_index, row_index + 1))
        else:
            rows_to_redact.append((row_index, row_index))

        row_index += 1

    print("\n" + "=" * 80)
    print(" Final rows to redact:", rows_to_redact)

    return rows_to_redact 