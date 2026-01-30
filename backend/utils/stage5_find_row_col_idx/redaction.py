# import fitz
# import os

# INCH_TO_PT = 72.0


# def redact_pdf_from_stream_with_spans(
#     pdf_stream: bytes,
#     output_pdf: str,
#     x1: float,
#     x2: float,
#     y_spans: set
# ):
#     output_dir = os.path.dirname(output_pdf)
#     if output_dir:
#         os.makedirs(output_dir, exist_ok=True)

#     doc = fitz.open(stream=pdf_stream, filetype="pdf")

#     x1_pt = x1 * INCH_TO_PT
#     x2_pt = x2 * INCH_TO_PT

#     for page_no, y1, y2 in y_spans:

#         if page_no < 0 or page_no >= len(doc):
#             continue
#         if y1 is None or y2 is None:
#             continue

#         page = doc[page_no]

#         y1_pt = y1 * INCH_TO_PT
#         y2_pt = y2 * INCH_TO_PT

#         rect = fitz.Rect(
#             min(x1_pt, x2_pt),
#             min(y1_pt, y2_pt),
#             max(x1_pt, x2_pt),
#             max(y1_pt, y2_pt),
#         )

#         page.add_redact_annot(rect, fill=(0, 0, 0))

#     for page in doc:
#         page.apply_redactions()

#     doc.save(output_pdf)
#     doc.close()

#     print("✅ Redacted PDF saved to:", output_pdf)

from io import BytesIO
import fitz
import os
from utils.logging.logger import get_logger
logger = get_logger(__name__)

INCH_TO_PT = 72.0


# def get_redacted_filename(original_path: str):
#     base, ext = os.path.splitext(original_path)
#     return f"{base}_redacted{ext}"


def redact_pdf_from_stream_with_spans(
    pdf_stream: bytes,
    x1: float,
    x2: float,
    y_spans: set
):
    # Create output folder if needed
    # output_dir = os.path.dirname(output_pdf)
    # if output_dir:
    #     os.makedirs(output_dir, exist_ok=True)

    # # Generate redacted filename
    # output_pdf = get_redacted_filename(output_pdf)

    # Open PDF from bytes
    doc = fitz.open(stream=pdf_stream, filetype="pdf")

    x1_pt = x1 * INCH_TO_PT
    x2_pt = x2 * INCH_TO_PT

    for page_no, y1, y2 in y_spans:

        if page_no < 0 or page_no >= len(doc):
            continue
        if y1 is None or y2 is None:
            continue

        page = doc[page_no]

        y1_pt = y1 * INCH_TO_PT
        y2_pt = y2 * INCH_TO_PT

        rect = fitz.Rect(
            min(x1_pt, x2_pt),
            min(y1_pt, y2_pt),
            max(x1_pt, x2_pt),
            max(y1_pt, y2_pt),
        )

        page.add_redact_annot(rect, fill=(0, 0, 0))

    # Apply all redactions
    for page in doc:
        page.apply_redactions()

    # Save redacted PDF
    output_buffer = BytesIO()  # Create an in-memory PDF
    doc.save(output_buffer)
    doc.close()

    redacted_bytes = output_buffer.getvalue()

    logger.info(
        "PDF redaction completed successfully (bytes)",
        extra={"output_size": len(redacted_bytes)},
    )

    return redacted_bytes

 