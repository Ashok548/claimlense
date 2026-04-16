"""
OCR Service — extracts raw text from uploaded hospital bills.
Supports:
  - PDF files via pdfplumber
  - Image files (JPG, PNG, TIFF) via pytesseract
"""

import io

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from a scanned image using pytesseract (Tesseract OCR)."""
    image = Image.open(io.BytesIO(file_bytes))
    # Use English + Hindi language packs for Indian hospital bills
    text = pytesseract.image_to_string(image, lang="eng")
    return text


def extract_text(file_bytes: bytes, file_type: str) -> tuple[str, str]:
    """
    Returns (raw_text, method_used).
    file_type: "pdf" | "image"
    """
    if file_type == "pdf":
        text = extract_text_from_pdf(file_bytes)
        method = "pdfplumber"
    else:
        text = extract_text_from_image(file_bytes)
        method = "pytesseract"

    return text, method
