"""AICTE bank-statement CSV import with UTR/amount auto-match — the one
*real* (non-simulated) piece of Phase 5's verification work, per the
brief. Matches ONLINE_SD instruments (online deposits) against statement
lines by UTR + amount, falling back to a fuzzy narration match when the
institution hasn't recorded a UTR.

Expected CSV columns: date, utr, narration, amount (header names are
case-insensitive and whitespace-tolerant).
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

AMOUNT_TOLERANCE = Decimal("0.01")


@dataclass
class StatementLine:
    row_number: int
    date: date | None
    utr: str
    narration: str
    amount: Decimal


@dataclass
class MatchResult:
    statement_line: StatementLine
    instrument_id: str | None
    confidence: str  # "exact_utr_amount" | "fuzzy_narration" | "no_match"
    reason: str


def parse_statement_csv(csv_bytes: bytes) -> list[StatementLine]:
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return []
    normalised_fields = {name: name.strip().lower() for name in reader.fieldnames}

    lines: list[StatementLine] = []
    for row_number, raw_row in enumerate(reader, start=2):  # header is row 1
        row = {
            normalised_fields[k]: v
            for k, v in raw_row.items()
            if k in normalised_fields
        }
        try:
            amount = Decimal(str(row.get("amount", "")).replace(",", "").strip())
        except InvalidOperation:
            continue
        parsed_date = _parse_date(row.get("date", ""))
        lines.append(
            StatementLine(
                row_number=row_number,
                date=parsed_date,
                utr=(row.get("utr") or "").strip(),
                narration=(row.get("narration") or "").strip(),
                amount=amount,
            )
        )
    return lines


def _parse_date(raw: str) -> date | None:
    raw = raw.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def match_statement_lines(
    lines: list[StatementLine], instruments: list
) -> list[MatchResult]:
    """`instruments` are ONLINE_SD-type Instrument rows (or any object
    with .id, .utr, .amount, .instrument_number) to match against."""
    results: list[MatchResult] = []
    for line in lines:
        match = _match_one(line, instruments)
        results.append(match)
    return results


def _match_one(line: StatementLine, instruments: list) -> MatchResult:
    if line.utr:
        for instrument in instruments:
            if instrument.utr and instrument.utr == line.utr:
                if abs(Decimal(instrument.amount) - line.amount) <= AMOUNT_TOLERANCE:
                    return MatchResult(
                        line,
                        str(instrument.id),
                        "exact_utr_amount",
                        f"UTR {line.utr} and amount both match",
                    )
                return MatchResult(
                    line,
                    None,
                    "no_match",
                    f"UTR {line.utr} matches instrument {instrument.id} but amount differs "
                    f"(statement {line.amount} vs declared {instrument.amount})",
                )

    # Fallback: narration contains the instrument number and amount matches
    # exactly — weaker signal, used when the institution never recorded a
    # UTR on the instrument.
    for instrument in instruments:
        narration_match = (
            instrument.instrument_number
            and instrument.instrument_number in line.narration
        )
        amount_match = (
            narration_match
            and abs(Decimal(instrument.amount) - line.amount) <= AMOUNT_TOLERANCE
        )
        if amount_match:
            return MatchResult(
                line,
                str(instrument.id),
                "fuzzy_narration",
                f"narration contains instrument number {instrument.instrument_number} and amount matches",
            )

    return MatchResult(
        line, None, "no_match", "no instrument matched by UTR or narration+amount"
    )
