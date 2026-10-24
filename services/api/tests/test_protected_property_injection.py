import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from app.authz import Principal, mask_identifier, serialize_instrument
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType


class InstrumentSubmissionPayload(BaseModel):
    """Pydantic model for submission: extra='forbid' rejects client injection of status/role/evidence_level."""

    model_config = ConfigDict(extra="forbid")

    instrument_number: str
    amount: Decimal
    tenor_months: int
    issue_date: date
    maturity_date: date


def test_extra_protected_properties_rejected_by_schema():
    """Client cannot inject status='VERIFIED', evidence_level='L2_BANK_CONFIRMED', or role='admin'."""
    valid_data = {
        "instrument_number": "FDR123456",
        "amount": "100000.00",
        "tenor_months": 12,
        "issue_date": "2026-01-01",
        "maturity_date": "2027-01-01",
    }
    # Valid parse
    req = InstrumentSubmissionPayload(**valid_data)
    assert req.instrument_number == "FDR123456"

    # Injected status=VERIFIED
    with pytest.raises(ValidationError) as exc:
        InstrumentSubmissionPayload(**{**valid_data, "status": "VERIFIED"})
    assert "Extra inputs are not permitted" in str(exc.value)

    # Injected evidence_level=L2_BANK_CONFIRMED
    with pytest.raises(ValidationError) as exc:
        InstrumentSubmissionPayload(
            **{**valid_data, "evidence_level": "L2_BANK_CONFIRMED"}
        )
    assert "Extra inputs are not permitted" in str(exc.value)

    # Injected role=admin
    with pytest.raises(ValidationError) as exc:
        InstrumentSubmissionPayload(**{**valid_data, "role": "admin"})
    assert "Extra inputs are not permitted" in str(exc.value)


def test_allow_list_serializer_masks_identifiers_for_unprivileged_roles():
    """Allow-list serializer serialize_instrument() masks instrument numbers as XXXX1234

    unless principal holds view_unmasked_identifiers permission.
    """

    class MockInstrument:
        id = uuid.uuid4()
        institution_id = uuid.uuid4()
        type = InstrumentType.FDR
        status = InstrumentStatus.ACTIVE
        evidence_level = EvidenceLevel.L2_BANK_CONFIRMED
        instrument_number = "987654321012"
        amount = Decimal("500000.00")
        issue_date = date(2025, 1, 1)
        maturity_date = date(2028, 1, 1)
        tenor_months = 36
        created_at = None

    instrument = MockInstrument()

    # Normal viewer / submitter
    viewer = Principal(
        id=uuid.uuid4(),
        email="viewer@example.com",
        full_name="Viewer",
        role=AppRole.INSTITUTION_VIEWER,
    )
    serialized_viewer = serialize_instrument(instrument, viewer)
    assert serialized_viewer["instrument_number"] == "XXXX1012"
    assert "987654321012" not in str(serialized_viewer)

    # Audit reviewer (does not hold view_unmasked_identifiers by default without explicit step-up)
    audit = Principal(
        id=uuid.uuid4(),
        email="auditor@example.com",
        full_name="Auditor",
        role=AppRole.AUDIT_REVIEWER,
    )
    serialized_audit = serialize_instrument(instrument, audit)
    assert serialized_audit["instrument_number"] == "XXXX1012"


def test_mask_identifier_utility():
    assert mask_identifier("12345678") == "XXXX5678"
    assert mask_identifier("12") == "XXXX"
    assert mask_identifier("") == ""
    assert mask_identifier(None) == ""
