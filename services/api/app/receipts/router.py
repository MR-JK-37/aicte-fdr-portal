"""Public receipt verification endpoint (SPEC §8.1 / F-20)."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from app.receipts.signer import verify_receipt_signature

router = APIRouter(prefix="/v1/public/receipts", tags=["Public Receipts"])


class PublicReceiptVerificationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    verified: bool
    receipt_id: str
    institution_code: str
    version_number: int
    version_hash_prefix: str
    issued_at: str
    message: str


@router.get("/verify", response_model=PublicReceiptVerificationResponse)
def verify_receipt(
    rid: str = Query(..., description="Receipt ID"),
    iid: str = Query(..., description="Instrument ID"),
    inst: str = Query(..., description="Institution Code"),
    ver: int = Query(..., description="Version Number"),
    h: str = Query(..., description="Content hash prefix"),
    ts: str = Query(..., description="Timestamp ISO"),
    sig: str = Query(..., description="Ed25519 signature"),
) -> PublicReceiptVerificationResponse:
    payload = {
        "rid": rid,
        "iid": iid,
        "inst": inst,
        "ver": ver,
        "h": h,
        "ts": ts,
    }

    is_valid = verify_receipt_signature(payload, sig)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "https://portal.aicte-india.org/problems/invalid-signature",
                "title": "Invalid Receipt Signature",
                "status": 400,
                "detail": "The receipt signature is invalid or tampered.",
            },
        )

    return PublicReceiptVerificationResponse(
        verified=True,
        receipt_id=rid,
        institution_code=inst,
        version_number=ver,
        version_hash_prefix=h,
        issued_at=ts,
        message="Cryptographic receipt authenticity confirmed by AICTE Regulation Bureau.",
    )
