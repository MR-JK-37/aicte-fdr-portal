from datetime import UTC, datetime

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.receipts.generator import generate_submission_receipt_pdf
from app.receipts.signer import sign_receipt_payload, verify_receipt_signature

client = TestClient(app)


def test_receipt_pdf_generation_and_valid_signature():
    ts = datetime.now(UTC)
    pdf_bytes, sig = generate_submission_receipt_pdf(
        receipt_id="REC-2026-001",
        instrument_id="11111111-2222-3333-4444-555555555555",
        instrument_number="FDR123456789",
        instrument_type="FDR",
        amount=1500000.0,
        institution_code="1-98765432",
        institution_name="National Engineering Institute",
        version_number=1,
        content_hash="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        submitted_at=ts,
    )
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

    # Verify signature over canonical payload
    payload = {
        "rid": "REC-2026-001",
        "iid": "11111111-2222-3333-4444-555555555555",
        "inst": "1-98765432",
        "ver": 1,
        "h": "abc1234567890abc",
        "ts": ts.isoformat(),
    }
    assert verify_receipt_signature(payload, sig) is True


def test_tampered_payload_fails_verification():
    ts = datetime.now(UTC)
    payload = {
        "rid": "REC-2026-002",
        "iid": "11111111-2222-3333-4444-555555555555",
        "inst": "1-98765432",
        "ver": 1,
        "h": "abc1234567890abc",
        "ts": ts.isoformat(),
    }
    sig = sign_receipt_payload(payload)

    # Tamper with version number
    tampered_payload = dict(payload)
    tampered_payload["ver"] = 2
    assert verify_receipt_signature(tampered_payload, sig) is False

    # Tamper with content hash
    tampered_hash = dict(payload)
    tampered_hash["h"] = "fake1234567890ab"
    assert verify_receipt_signature(tampered_hash, sig) is False


def test_public_receipt_verification_endpoint():
    ts = datetime.now(UTC)
    payload = {
        "rid": "REC-2026-003",
        "iid": "22222222-3333-4444-5555-666666666666",
        "inst": "1-55555555",
        "ver": 1,
        "h": "deadbeef12345678",
        "ts": ts.isoformat(),
    }
    sig = sign_receipt_payload(payload)

    # Valid request
    res = client.get(
        "/v1/public/receipts/verify",
        params={
            "rid": payload["rid"],
            "iid": payload["iid"],
            "inst": payload["inst"],
            "ver": payload["ver"],
            "h": payload["h"],
            "ts": payload["ts"],
            "sig": sig,
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["verified"] is True
    assert data["receipt_id"] == "REC-2026-003"
    assert data["institution_code"] == "1-55555555"
    assert data["version_hash_prefix"] == "deadbeef12345678"

    # Invalid signature request
    res_bad = client.get(
        "/v1/public/receipts/verify",
        params={
            "rid": payload["rid"],
            "iid": payload["iid"],
            "inst": payload["inst"],
            "ver": payload["ver"],
            "h": payload["h"],
            "ts": payload["ts"],
            "sig": "tampered_signature_string",
        },
    )
    assert res_bad.status_code == status.HTTP_400_BAD_REQUEST
