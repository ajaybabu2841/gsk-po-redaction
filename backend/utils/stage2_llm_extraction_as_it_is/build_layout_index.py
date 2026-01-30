from rapidfuzz import fuzz
import re


def polygon_y_bounds(polygon):
    ys = polygon[1::2]
    return min(ys), max(ys)


def normalize_medicine_name(text: str) -> str:
    if not text:
        return ""

    text = text.upper()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    # Remove common noise words (tune carefully)
    noise_words = [
        "PHARMACEUTICALS", "PHARMA", "LTD", "LIMITED",
        "INDIA", "PRIVATE", "PVT"
    ]
    for w in noise_words:
        text = re.sub(rf"\b{w}\b", " ", text)

    # Collapse spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_layout_index_for_non_gsk(
    layout_result,
    non_gsk_med_list,
    fuzzy_threshold=85,
):
    """
    Returns:
    {
      normalized_non_gsk_med: [
        {
          "page_no": int,
          "y1": float,
          "y2": float,
          "lines": [str],
        }
      ]
    }
    """

    # if competitor_brands is None:
    competitor_brands = ["CIPLA", "ABBOTT", "TORRENT", "LUPIN", "SANOFI","BIOCON","BHARAT"]

    # Normalize non-GSK medicine names once
    normalized_non_gsk = {
        normalize_medicine_name(med): med
        for med in non_gsk_med_list
    }

    padding_y = 0.01

    layout_index = {}

    for page_idx, page in enumerate(layout_result.pages):
        page_no = page.page_number - 1  # fitz is 0-based

        # Convert ADI line objects → simple dicts
        page_lines = []
        for line in page.lines:
            page_lines.append({
                "content": line.content,
                "polygon": line.polygon,
            })

        for norm_med in normalized_non_gsk.keys():
            matched_lines = []

            for line in page_lines:
                norm_line = normalize_medicine_name(line["content"])

                score = fuzz.ratio(norm_med, norm_line)

                if score >= fuzzy_threshold:
                    matched_lines.append(line)

            if not matched_lines:
                continue

            # Store each matched line as a separate entry
            for line in matched_lines:
                y1, y2 = polygon_y_bounds(line["polygon"])

                entry = {
                    "page_no": page_no,
                    "y1": y1 + padding_y,
                    "y2": y2 - padding_y,
                    "lines": [line["content"]],
                }

                # LOG THE ENTRY DATA
                print(f"Creating entry for medicine: {norm_med}")
                print(f"  Page: {entry['page_no']}")
                print(f"  Y1: {entry['y1']}")
                print(f"  Y2: {entry['y2']}")
                print(f"  Lines: {entry['lines']}")
                print("-" * 50)

                layout_index.setdefault(norm_med, []).append(entry)

        # STEP 2: Match by competitor brand names
        for line in page_lines:
            line_upper = line["content"].upper()
            
            # Check if any competitor brand appears in this line
            matched_brand = None
            for brand in competitor_brands:
                if brand in line_upper:
                    matched_brand = brand
                    break
            
            if matched_brand:
                y1, y2 = polygon_y_bounds(line["polygon"])
                
                entry = {
                    "page_no": page_no,
                    "y1": y1 + padding_y,
                    "y2": y2 - padding_y,
                    "lines": [line["content"]],
                }
                
                # Use a special key for brand-based matches
                brand_key = f"BRAND_{matched_brand}"
                
                # LOG THE ENTRY DATA
                print(f"Creating entry for competitor brand: {matched_brand}")
                print(f"  Page: {entry['page_no']}")
                print(f"  Y1: {entry['y1']}")
                print(f"  Y2: {entry['y2']}")
                print(f"  Lines: {entry['lines']}")
                print("-" * 50)

                layout_index.setdefault(brand_key, []).append(entry)

    return layout_index