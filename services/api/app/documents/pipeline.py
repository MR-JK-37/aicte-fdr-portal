"""Orchestrates the full upload pipeline: quarantine -> ClamAV ->
magic-byte check -> PDF sanitise -> hash (SHA-256 + pHash) -> encrypted
store -> OCR -> redact -> extract -> validate -> forgery signals ->
officer confirms (L1).

Every stage outcome is written to the audit log, pass or fail, so a
rejected upload is as traceable as an accepted one.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.documents import forgery, hashing, ocr, redaction, security_scan
from app.documents.extraction import FDRExtractedFields, FDRExtractor, RegexFDRExtractor
from app.documents.validation import ValidationFlag, validate_extracted_fields
from app.models.core import Document, Instrument
from app.models.enums import EvidenceLevel
from app.storage import put_object


class DocumentRejectedError(Exception):
    def __init__(self, stage: str, reason: str):
        self.stage = stage
        self.reason = reason
        super().__init__(f"document rejected at stage '{stage}': {reason}")


@dataclass
class PipelineResult:
    document: Document
    extracted: FDRExtractedFields
    validation_flags: list[ValidationFlag] = field(default_factory=list)
    forgery_signals: list[forgery.ForgerySignal] = field(default_factory=list)


def run_pipeline(
    session: Session,
    instrument: Instrument,
    *,
    data: bytes,
    declared_mime_type: str,
    uploaded_by: str | None,
    extractor: FDRExtractor | None = None,
) -> PipelineResult:
    extractor = extractor or RegexFDRExtractor()

    def _audit(stage: str, passed: bool, detail: str) -> None:
        append_audit_entry(
            session,
            action=f"document.{stage}",
            entity_type="instrument",
            entity_id=str(instrument.id),
            after={"passed": passed, "detail": detail},
            actor_id=uploaded_by,
            institution_id=str(instrument.institution_id),
        )

    magic_result = security_scan.check_magic_bytes(data, declared_mime_type)
    _audit("magic_byte_check", magic_result.passed, magic_result.reason)
    if not magic_result.passed:
        raise DocumentRejectedError("magic_byte_check", magic_result.reason)

    av_result = security_scan.scan_for_malware(data)
    _audit("clamav_scan", av_result.passed, av_result.reason)
    if not av_result.passed:
        raise DocumentRejectedError("clamav_scan", av_result.reason)

    clean_data = data
    if declared_mime_type == "application/pdf":
        sanitise_result, sanitised = security_scan.sanitise_pdf(data)
        _audit("pdf_sanitise", sanitise_result.passed, sanitise_result.reason)
        if not sanitise_result.passed:
            raise DocumentRejectedError("pdf_sanitise", sanitise_result.reason)
        clean_data = sanitised

    sha256 = hashing.sha256_hex(clean_data)
    phash = hashing.perceptual_hash(clean_data, declared_mime_type)

    storage_key = f"instruments/{instrument.id}/{sha256}"
    put_object(storage_key, clean_data, content_type=declared_mime_type)

    document = Document(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        storage_key=storage_key,
        sha256=sha256,
        phash=phash,
        mime_type=declared_mime_type,
        status="scanned_clean",
        uploaded_by=uploaded_by,
    )
    session.add(document)
    session.flush()
    _audit("stored", True, f"stored at {storage_key}")

    text = ocr.extract_text(clean_data, declared_mime_type)
    redacted_text, _token_map = redaction.redact(text)
    extracted = extractor.extract(redacted_text)
    _audit("extracted", True, extracted.model_dump_json())

    validation_flags = validate_extracted_fields(extracted)
    for flag in validation_flags:
        _audit("validation_flag", False, f"{flag.field}: {flag.message}")

    forgery_signals: list[forgery.ForgerySignal] = []
    if extracted.instrument_number:
        dup = forgery.check_duplicate_instrument_number(
            session,
            instrument.institution_id,
            extracted.instrument_number,
            instrument.id,
        )
        if dup:
            forgery_signals.append(dup)
    if phash:
        dup_phash = forgery.check_duplicate_phash(session, phash, document.id)
        if dup_phash:
            forgery_signals.append(dup_phash)
    pdf_meta_signal = (
        forgery.check_pdf_producer_metadata(clean_data)
        if declared_mime_type == "application/pdf"
        else None
    )
    if pdf_meta_signal:
        forgery_signals.append(pdf_meta_signal)
    for signal in forgery_signals:
        _audit("forgery_signal", False, f"{signal.signal}: {signal.detail}")

    # Evidence level moves to L1 only on explicit officer confirmation
    # (confirm_extraction, below) — never automatically, even when the
    # pipeline found no flags. "Officer confirms (L1)" in the brief means
    # a human decision, not an automatic pass-through.
    return PipelineResult(
        document=document,
        extracted=extracted,
        validation_flags=validation_flags,
        forgery_signals=forgery_signals,
    )


OFFICER_CONFIRM_ROLES = frozenset({"scrutiny_officer", "finance_verifier"})


def confirm_extraction(
    session: Session,
    instrument: Instrument,
    *,
    actor_role: str,
    actor_id: str | None,
    reason: str,
) -> None:
    """The human-in-the-loop step that actually advances evidence_level to
    L1 after an officer has reviewed the extracted fields against the
    source document. Deliberately separate from run_pipeline — automatic
    promotion would defeat the point of an evidence-level ladder."""
    if actor_role not in OFFICER_CONFIRM_ROLES:
        raise PermissionError(
            f"role '{actor_role}' may not confirm document extraction"
        )
    if not reason or not reason.strip():
        raise ValueError("a non-empty reason is required to confirm extraction")

    before_level = instrument.evidence_level
    instrument.evidence_level = EvidenceLevel.L1_EXTRACTED
    session.flush()
    append_audit_entry(
        session,
        action="instrument.evidence_level_confirmed",
        entity_type="instrument",
        entity_id=str(instrument.id),
        before={"evidence_level": before_level.value},
        after={
            "evidence_level": EvidenceLevel.L1_EXTRACTED.value,
            "reason": reason,
            "actor_role": actor_role,
        },
        actor_id=actor_id,
        institution_id=str(instrument.institution_id),
    )
