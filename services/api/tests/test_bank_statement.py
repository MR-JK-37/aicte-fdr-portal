import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.verification.bank_statement import match_statement_lines, parse_statement_csv


@dataclass
class FakeInstrument:
    id: str
    instrument_number: str
    amount: Decimal
    utr: str | None


def test_parse_statement_csv_basic():
    csv_bytes = (
        b"Date,UTR,Narration,Amount\n"
        b"01-01-2025,UTR123,NEFT FROM ABC COLLEGE,500000\n"
        b"02-01-2025,UTR456,NEFT FDR123456 XYZ,1000000\n"
    )
    lines = parse_statement_csv(csv_bytes)
    assert len(lines) == 2
    assert lines[0].utr == "UTR123"
    assert lines[0].amount == Decimal(500000)
    assert lines[1].narration == "NEFT FDR123456 XYZ"


def test_exact_utr_and_amount_match():
    instrument = FakeInstrument(
        id=str(uuid.uuid4()),
        instrument_number="FDR1",
        amount=Decimal(500000),
        utr="UTR123",
    )
    csv_bytes = b"Date,UTR,Narration,Amount\n01-01-2025,UTR123,payment,500000\n"
    lines = parse_statement_csv(csv_bytes)
    results = match_statement_lines(lines, [instrument])
    assert results[0].confidence == "exact_utr_amount"
    assert results[0].instrument_id == instrument.id


def test_utr_match_but_amount_mismatch_is_no_match():
    instrument = FakeInstrument(
        id=str(uuid.uuid4()),
        instrument_number="FDR1",
        amount=Decimal(500000),
        utr="UTR123",
    )
    csv_bytes = b"Date,UTR,Narration,Amount\n01-01-2025,UTR123,payment,400000\n"
    lines = parse_statement_csv(csv_bytes)
    results = match_statement_lines(lines, [instrument])
    assert results[0].confidence == "no_match"
    assert results[0].instrument_id is None


def test_fuzzy_narration_fallback_when_no_utr_recorded():
    instrument = FakeInstrument(
        id=str(uuid.uuid4()),
        instrument_number="FDR999888",
        amount=Decimal(500000),
        utr=None,
    )
    csv_bytes = (
        b"Date,UTR,Narration,Amount\n01-01-2025,,NEFT ref FDR999888 college,500000\n"
    )
    lines = parse_statement_csv(csv_bytes)
    results = match_statement_lines(lines, [instrument])
    assert results[0].confidence == "fuzzy_narration"
    assert results[0].instrument_id == instrument.id


def test_no_match_when_nothing_lines_up():
    instrument = FakeInstrument(
        id=str(uuid.uuid4()), instrument_number="FDR1", amount=Decimal(500000), utr=None
    )
    csv_bytes = b"Date,UTR,Narration,Amount\n01-01-2025,,unrelated payment,999999\n"
    lines = parse_statement_csv(csv_bytes)
    results = match_statement_lines(lines, [instrument])
    assert results[0].confidence == "no_match"
    assert results[0].instrument_id is None
