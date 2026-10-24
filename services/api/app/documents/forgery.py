"""Forgery/duplicate signals that need the database (cross-institution
checks), as opposed to validation.py's pure per-document rules.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Document, Instrument


@dataclass
class ForgerySignal:
    signal: str
    severity: str
    detail: str


def check_duplicate_instrument_number(
    session: Session, institution_id, instrument_number: str, exclude_instrument_id
) -> ForgerySignal | None:
    """Same instrument number claimed by a *different* institution is a
    strong forgery/duplicate-use signal (the brief's example: "same FDR
    number+IFSC at two institutions"). This check must run with
    bureau-side RLS context to see across institutions at all — that
    cross-tenant visibility is the entire point of the check, and is why
    it belongs in a worker/agent step, not something the institution's
    own session could ever evaluate correctly under RLS."""
    query = select(Instrument).where(
        Instrument.instrument_number == instrument_number,
        Instrument.institution_id != institution_id,
    )
    if exclude_instrument_id is not None:
        query = query.where(Instrument.id != exclude_instrument_id)
    match = session.execute(query).scalars().first()
    if match is not None:
        return ForgerySignal(
            "duplicate_instrument_number",
            "high",
            f"instrument number '{instrument_number}' already exists on instrument {match.id} "
            f"at a different institution ({match.institution_id})",
        )
    return None


def check_duplicate_phash(
    session: Session, phash: str, exclude_document_id
) -> ForgerySignal | None:
    """Exact perceptual-hash match against a different document is a
    strong signal of the same scanned page being resubmitted (possibly
    for a different institution/instrument)."""
    if phash is None:
        return None
    query = select(Document).where(Document.phash == phash)
    if exclude_document_id is not None:
        query = query.where(Document.id != exclude_document_id)
    match = session.execute(query).scalars().first()
    if match is not None:
        return ForgerySignal(
            "duplicate_phash",
            "high",
            f"perceptual hash matches an existing document {match.id} (instrument {match.instrument_id})",
        )
    return None


def check_pdf_producer_metadata(data: bytes) -> ForgerySignal | None:
    """Flags PDF producer/creator metadata associated with common editing
    tools rather than scan/print pipelines — a soft signal, not proof."""
    import io

    from pypdf import PdfReader

    suspicious_producers = {"photoshop", "gimp", "canva", "microsoft word"}
    try:
        reader = PdfReader(io.BytesIO(data))
        meta = reader.metadata or {}
        producer = str(meta.get("/Producer", "")).lower()
        creator = str(meta.get("/Creator", "")).lower()
        for tool in suspicious_producers:
            if tool in producer or tool in creator:
                return ForgerySignal(
                    "pdf_producer_metadata",
                    "medium",
                    f"PDF metadata indicates editing tool usage (producer='{producer}', creator='{creator}')",
                )
    except Exception:  # noqa: BLE001 — best-effort signal, not a gate; see docstring
        return None
    return None
