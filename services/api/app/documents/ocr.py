"""Local OCR via Tesseract (per the brief: "local OCR (PaddleOCR or
Tesseract)" — Tesseract is chosen for a much lighter container footprint,
which matters on the 2 OCPU/12GB Oracle Always Free target).
"""

import io

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def rasterise(data: bytes, mime_type: str, dpi: int = 300) -> list[Image.Image]:
    if mime_type == "application/pdf":
        return convert_from_bytes(data, dpi=dpi)
    return [Image.open(io.BytesIO(data))]


def extract_text(data: bytes, mime_type: str) -> str:
    pages = rasterise(data, mime_type)
    return "\n".join(pytesseract.image_to_string(page) for page in pages)
