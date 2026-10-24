import io
import os
from dataclasses import dataclass, field

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


@dataclass
class OCRToken:
    text: str
    page: int
    left: int
    top: int
    width: int
    height: int
    confidence: float


@dataclass
class OCRResult:
    raw_text: str
    tokens: list[OCRToken] = field(default_factory=list)
    engine: str = "tesseract-v5.5.3"
    status: str = "AVAILABLE"  # "AVAILABLE" | "UNAVAILABLE"
    error: str | None = None


def rasterise(data: bytes, mime_type: str, dpi: int = 300) -> list[Image.Image]:
    if mime_type == "application/pdf":
        return convert_from_bytes(data, dpi=dpi)
    return [Image.open(io.BytesIO(data))]


def extract_ocr_data(data: bytes, mime_type: str) -> OCRResult:
    """Extracts raw text and word-level bounding boxes and confidences per page.
    Returns honest UNAVAILABLE status if OCR is disabled or fails.
    """
    if os.environ.get("DISABLE_OCR", "").lower() in ("1", "true", "yes"):
        return OCRResult(
            raw_text="",
            tokens=[],
            status="UNAVAILABLE",
            error="OCR is disabled by configuration",
        )

    try:
        pages = rasterise(data, mime_type)
        all_tokens: list[OCRToken] = []
        page_texts: list[str] = []

        for page_idx, page in enumerate(pages, start=1):
            page_text = pytesseract.image_to_string(page)
            page_texts.append(page_text)

            data_dict = pytesseract.image_to_data(
                page, output_type=pytesseract.Output.DICT
            )
            n_boxes = len(data_dict.get("text", []))
            for i in range(n_boxes):
                w_text = data_dict["text"][i].strip()
                if not w_text:
                    continue
                conf = float(data_dict["conf"][i])
                conf_norm = max(0.0, conf) / 100.0 if conf >= 0 else 0.5
                all_tokens.append(
                    OCRToken(
                        text=w_text,
                        page=page_idx,
                        left=data_dict["left"][i],
                        top=data_dict["top"][i],
                        width=data_dict["width"][i],
                        height=data_dict["height"][i],
                        confidence=round(conf_norm, 2),
                    )
                )

        full_text = "\n".join(page_texts)
        return OCRResult(
            raw_text=full_text,
            tokens=all_tokens,
            engine="tesseract-v5.5.3",
            status="AVAILABLE",
        )
    except (pytesseract.TesseractError, OSError, ValueError, RuntimeError) as exc:
        return OCRResult(
            raw_text="",
            tokens=[],
            status="UNAVAILABLE",
            error=str(exc),
        )


def extract_text(data: bytes, mime_type: str) -> str:
    res = extract_ocr_data(data, mime_type)
    return res.raw_text
