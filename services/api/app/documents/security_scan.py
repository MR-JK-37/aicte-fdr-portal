"""Upload security pipeline: magic-byte check, ClamAV scan, PDF sanitising.

Pipeline order per the brief: quarantine -> ClamAV -> magic-byte check ->
PDF sanitise -> hash. Each stage returns a pass/fail + reason rather than
raising, so the caller (document_pipeline.py) can log every stage's
outcome to the audit log even on rejection.
"""

import io
from dataclasses import dataclass

import clamd
import magic
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from app.config import settings

# Only these MIME types are accepted for FDR/instrument document uploads.
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}


@dataclass
class ScanResult:
    passed: bool
    reason: str


def check_magic_bytes(data: bytes, declared_mime_type: str) -> ScanResult:
    """Detects the real file type from content, not the client-supplied
    filename/Content-Type, and rejects any mismatch or disallowed type —
    this is what stops a renamed .exe uploaded as "scan.pdf"."""
    detected = magic.from_buffer(data, mime=True)
    if detected not in ALLOWED_MIME_TYPES:
        return ScanResult(
            False, f"detected MIME type '{detected}' is not an allowed document type"
        )
    if detected != declared_mime_type:
        return ScanResult(
            False,
            f"declared MIME type '{declared_mime_type}' does not match detected type '{detected}'",
        )
    return ScanResult(True, f"magic-byte check passed ({detected})")


def scan_for_malware(data: bytes) -> ScanResult:
    try:
        client = clamd.ClamdNetworkSocket(
            host=settings.clamav_host, port=settings.clamav_port
        )
        result = client.instream(io.BytesIO(data))
    except (clamd.ConnectionError, OSError) as exc:
        # Fail closed: if the scanner is unreachable, the upload is rejected
        # rather than silently skipped. A quarantined-but-unscanned document
        # must never reach storage.
        return ScanResult(
            False, f"ClamAV unreachable, rejecting upload fail-closed: {exc}"
        )

    status, signature = result["stream"]
    if status == "FOUND":
        return ScanResult(False, f"malware signature detected: {signature}")
    return ScanResult(True, "clean")


def sanitise_pdf(data: bytes) -> tuple[ScanResult, bytes | None]:
    """Rebuilds the PDF via pypdf, which drops embedded JavaScript, launch
    actions and most other active-content constructs that aren't plain
    page content/annotations by virtue of not being copied over into the
    rebuilt document."""
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            return ScanResult(False, "encrypted PDFs are not accepted"), None
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        return ScanResult(True, "PDF rebuilt/sanitised"), out.getvalue()
    except PdfReadError as exc:
        return ScanResult(False, f"unreadable/corrupt PDF: {exc}"), None
