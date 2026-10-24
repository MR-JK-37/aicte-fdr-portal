"""Document Vault & Upload Pipeline Router (F-04 / SPEC §8.1)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.documents import hashing
from app.documents.security_scan import (
    check_magic_bytes,
    sanitise_pdf,
    scan_for_malware,
)
from app.lifecycle import SYSTEM_ROLE, apply_document_transition
from app.models.core import Document, Instrument
from app.models.enums import DocumentStatus
from app.problem_json import ForbiddenError, NotFoundError
from app.storage import presigned_get_url, presigned_put_url, put_object

router = APIRouter(prefix="/v1/documents", tags=["Document Vault"])

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB cap per SPEC §8.1


# --- Schemas ---
class UploadIntentRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: uuid.UUID
    declared_mime_type: str = Field(
        ..., pattern="^(application/pdf|image/jpeg|image/png|image/tiff)$"
    )
    file_size_bytes: int = Field(..., gt=0, le=MAX_UPLOAD_SIZE_BYTES)
    document_category: str = "fdr_copy"


class UploadIntentResponse(BaseModel):
    document_id: uuid.UUID
    instrument_id: uuid.UUID
    quarantine_key: str
    presigned_upload_url: str
    max_size_bytes: int
    expires_in_seconds: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    instrument_id: uuid.UUID
    storage_key: str
    sha256: str
    phash: str | None = None
    mime_type: str
    status: str
    created_at: datetime


class DownloadResponse(BaseModel):
    document_id: uuid.UUID
    sha256: str
    download_url: str
    expires_in_seconds: int


# --- Endpoints ---
@router.post(
    "/upload-intent",
    response_model=UploadIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_upload_intent(
    payload: UploadIntentRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.UPLOAD_EVIDENCE)),
    db: Session = Depends(get_db),
) -> UploadIntentResponse:
    """Issues upload intent with quarantine key and presigned PUT URL (F-04)."""
    instrument = db.execute(
        select(Instrument).where(Instrument.id == payload.instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", payload.instrument_id)

    # Scope check
    if (
        principal.institution_id
        and principal.institution_id != instrument.institution_id
    ):
        raise ForbiddenError(
            "Cannot upload documents for another institution's instrument"
        )

    doc_id = uuid.uuid4()
    quarantine_key = f"quarantine/{instrument.id}/{doc_id}"

    document = Document(
        id=doc_id,
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        storage_key=quarantine_key,
        sha256="PENDING_UPLOAD",
        mime_type=payload.declared_mime_type,
        status=DocumentStatus.UPLOAD_INTENT.value,
        uploaded_by=principal.id,
    )
    db.add(document)
    db.flush()

    append_audit_entry(
        db,
        action="document.upload_intent_created",
        entity_type="document",
        entity_id=str(doc_id),
        after={
            "quarantine_key": quarantine_key,
            "declared_mime_type": payload.declared_mime_type,
            "file_size_bytes": payload.file_size_bytes,
        },
        actor_id=str(principal.id),
        institution_id=str(instrument.institution_id),
    )

    db.commit()

    presigned_url = presigned_put_url(quarantine_key, expires_in=900)

    return UploadIntentResponse(
        document_id=doc_id,
        instrument_id=instrument.id,
        quarantine_key=quarantine_key,
        presigned_upload_url=presigned_url,
        max_size_bytes=MAX_UPLOAD_SIZE_BYTES,
        expires_in_seconds=900,
    )


@router.post(
    "/upload-direct",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def direct_upload_and_pipeline(
    instrument_id: uuid.UUID = Query(...),
    declared_mime_type: str = Query("application/pdf"),
    file: UploadFile = File(...),
    principal: Principal = Depends(require_permission(PermissionVerb.UPLOAD_EVIDENCE)),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Direct upload pipeline executing all checks synchronously (F-04):
    1. Magic bytes & MIME verification
    2. ClamAV anti-malware scan
    3. PDF sanitisation (strip JS/launch actions)
    4. SHA-256 + perceptual hash calculation
    5. Move to vault
    6. Transition status UPLOAD_INTENT -> QUARANTINED -> SCANNING -> ACCEPTED
    """
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    if (
        principal.institution_id
        and principal.institution_id != instrument.institution_id
    ):
        raise ForbiddenError(
            "Cannot upload documents for another institution's instrument"
        )

    data = file.file.read()
    if len(data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
        )

    # 1. Magic byte check
    magic_res = check_magic_bytes(data, declared_mime_type)
    if not magic_res.passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File rejected by magic-byte verification: {magic_res.reason}",
        )

    # 2. ClamAV scan
    av_res = scan_for_malware(data)
    if not av_res.passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File rejected by antivirus scan: {av_res.reason}",
        )

    # 3. PDF sanitise
    clean_data = data
    if declared_mime_type == "application/pdf":
        sanitise_res, sanitised = sanitise_pdf(data)
        if not sanitise_res.passed or not sanitised:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF sanitisation failed: {sanitise_res.reason}",
            )
        clean_data = sanitised

    # 4. Hash
    sha256 = hashing.sha256_hex(clean_data)
    phash = hashing.perceptual_hash(clean_data, declared_mime_type)

    # 5. Move to vault in storage
    vault_key = f"vault/{instrument.id}/{sha256}"
    put_object(vault_key, clean_data, content_type=declared_mime_type)

    doc_id = uuid.uuid4()
    document = Document(
        id=doc_id,
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        storage_key=vault_key,
        sha256=sha256,
        phash=phash,
        mime_type=declared_mime_type,
        status=DocumentStatus.UPLOAD_INTENT.value,
        uploaded_by=principal.id,
    )
    db.add(document)
    db.flush()

    role_str = (
        principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role)
    )
    apply_document_transition(
        db,
        document,
        DocumentStatus.QUARANTINED,
        actor_role=role_str,
        actor_id=str(principal.id),
        reason="File uploaded to quarantine buffer",
        reason_code="QUARANTINE_BUFFER",
    )
    apply_document_transition(
        db,
        document,
        DocumentStatus.SCANNING,
        actor_role=SYSTEM_ROLE,
        actor_id=str(principal.id),
        reason="Beginning ClamAV scan and PDF sanitisation",
        reason_code="SECURITY_SCAN_START",
    )
    apply_document_transition(
        db,
        document,
        DocumentStatus.ACCEPTED,
        actor_role=SYSTEM_ROLE,
        actor_id=str(principal.id),
        reason="Document passed magic bytes, ClamAV scan, and PDF sanitisation",
        reason_code="SECURITY_CHECKS_PASSED",
    )

    res = DocumentResponse.model_validate(document)
    db.commit()
    return res


@router.get("/{document_id}/download", response_model=DownloadResponse)
def get_download_url(
    document_id: uuid.UUID,
    principal: Principal = Depends(
        require_permission(PermissionVerb.DOWNLOAD_EVIDENCE)
    ),
    db: Session = Depends(get_db),
) -> DownloadResponse:
    """Mints short-lived signed download URL (F-04).
    Logs download event to audit chain.
    """
    doc = db.execute(
        select(Document).where(Document.id == document_id)
    ).scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", document_id)

    # Log access event (per MASTER_PROMPT §F-04 / §F-18)
    append_audit_entry(
        db,
        action="document.download_requested",
        entity_type="document",
        entity_id=str(doc.id),
        after={
            "sha256": doc.sha256,
            "storage_key": doc.storage_key,
        },
        actor_id=str(principal.id),
        institution_id=str(doc.institution_id),
    )
    db.commit()

    download_url = presigned_get_url(doc.storage_key, expires_in=300)

    return DownloadResponse(
        document_id=doc.id,
        sha256=doc.sha256,
        download_url=download_url,
        expires_in_seconds=300,
    )
