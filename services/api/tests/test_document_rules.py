from datetime import date
from decimal import Decimal

from app.documents.extraction import FDRExtractedFields
from app.documents.redaction import redact, rehydrate
from app.documents.validation import validate_extracted_fields


def test_redaction_tokenises_and_rehydrates_pii():
    text = "Contact 9876543210, PAN ABCDE1234F, IFSC SBIN0001234."
    redacted, token_map = redact(text)
    assert "9876543210" not in redacted
    assert "ABCDE1234F" not in redacted
    assert "SBIN0001234" not in redacted
    restored = rehydrate(redacted, token_map)
    assert restored == text


def test_valid_fields_produce_no_flags():
    fields = FDRExtractedFields(
        instrument_number="FDR123456",
        ifsc="SBIN0001234",
        amount=Decimal(500000),
        amount_words="Rupees Five Lakh Only",
        issue_date=date(2024, 1, 1),
        maturity_date=date(2025, 1, 1),
        tenor_months=12,
    )
    assert validate_extracted_fields(fields) == []


def test_bad_ifsc_format_flagged():
    fields = FDRExtractedFields(ifsc="NOTANIFSC")
    flags = validate_extracted_fields(fields)
    assert any(f.field == "ifsc" for f in flags)


def test_maturity_not_equal_issue_plus_tenor_flagged():
    fields = FDRExtractedFields(
        issue_date=date(2024, 1, 1), maturity_date=date(2025, 6, 1), tenor_months=12
    )
    flags = validate_extracted_fields(fields)
    assert any(f.field == "maturity_date" for f in flags)


def test_maturity_before_issue_flagged():
    fields = FDRExtractedFields(
        issue_date=date(2024, 6, 1), maturity_date=date(2024, 1, 1)
    )
    flags = validate_extracted_fields(fields)
    assert any(f.field == "maturity_date" and "after" in f.message for f in flags)


def test_amount_words_mismatch_flagged():
    fields = FDRExtractedFields(
        amount=Decimal(500000), amount_words="Rupees Ten Lakh Only"
    )
    flags = validate_extracted_fields(fields)
    assert any(f.field == "amount" for f in flags)


def test_amount_words_match_not_flagged():
    fields = FDRExtractedFields(
        amount=Decimal(500000), amount_words="Rupees Five Lakh Only"
    )
    flags = validate_extracted_fields(fields)
    assert not any(f.field == "amount" for f in flags)


def test_nonpositive_amount_flagged():
    fields = FDRExtractedFields(amount=Decimal(0))
    flags = validate_extracted_fields(fields)
    assert any(f.field == "amount" and "positive" in f.message for f in flags)
