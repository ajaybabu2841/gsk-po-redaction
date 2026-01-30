
from pdf2image import convert_from_bytes
from PIL import Image
from typing import List

def pdf_bytes_to_images(pdf_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
    """
    Convert PDF bytes into a list of PIL Images (one per page).

    Args:
        pdf_bytes (bytes): Raw PDF file bytes
        dpi (int): Image resolution (default: 300)

    Returns:
        List[PIL.Image]: List of page images
    """
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    return images

 