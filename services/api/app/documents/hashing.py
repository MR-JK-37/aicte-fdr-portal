import hashlib
import io

import imagehash
from pdf2image import convert_from_bytes
from PIL import Image


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def perceptual_hash(data: bytes, mime_type: str) -> str | None:
    """Perceptual hash of the first page/image, used to catch the same
    scanned FDR re-submitted (possibly re-encoded) across institutions —
    a duplicate-instrument signal independent of the SHA-256, which would
    differ after any re-save/re-compress."""
    try:
        if mime_type == "application/pdf":
            pages = convert_from_bytes(data, first_page=1, last_page=1, dpi=150)
            image = pages[0]
        else:
            image = Image.open(io.BytesIO(data))
        return str(imagehash.phash(image))
    except Exception:  # noqa: BLE001 — best-effort signal, not a gate; see docstring
        # Perceptual hashing is a forgery *signal*, not a gate — a page
        # that fails to rasterise still passes the rest of the pipeline;
        # phash just comes back absent for the duplicate-detection query.
        return None
