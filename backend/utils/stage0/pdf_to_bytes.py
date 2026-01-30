import sys
from pathlib import Path

PDF_FOLDER = Path("PDF_INPUT")

def load_pdf_as_bytes(pdf_name: str) -> bytes:
    pdf_path = PDF_FOLDER / pdf_name

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    return pdf_bytes
 