"""Bank Statement Parsers for MT940, CAMT.053 (ISO 20022 XML), and CSV (F-07).

Separates valid lines from quarantined (malformed) lines with granular reasons:
- Valid lines -> ParsedStatementLine
- Invalid lines -> QuarantinedLine (quarantined with line number, reason, and raw content)
"""

import csv
import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


@dataclass
class ParsedStatementLine:
    line_number: int
    booking_date: date | None
    value_date: date | None
    amount: Decimal
    currency: str
    utr: str
    narration: str


@dataclass
class QuarantinedLine:
    line_number: int
    reason: str
    raw_content: str


@dataclass
class ParseResult:
    file_format: str
    lines: list[ParsedStatementLine] = field(default_factory=list)
    quarantined: list[QuarantinedLine] = field(default_factory=list)


def parse_date_flexible(raw: str) -> date | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y%m%d",
        "%y%m%d",
        "%d.%m.%Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_statement_csv(content: bytes) -> ParseResult:
    """Parses CSV statement with flexible header normalization and line-by-line quarantine."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return ParseResult(
            file_format="CSV",
            quarantined=[QuarantinedLine(1, "Missing CSV header row", text[:100])],
        )

    # Normalize header names
    field_map: dict[str, str] = {}
    for f in reader.fieldnames:
        clean = f.strip().lower()
        if clean in ("date", "booking_date", "txn_date", "transaction_date"):
            field_map["date"] = f
        elif clean in ("val_date", "value_date"):
            field_map["val_date"] = f
        elif clean in ("amount", "amt", "deposit_amount", "credit"):
            field_map["amount"] = f
        elif clean in ("utr", "ref", "reference", "utr_number", "txn_id"):
            field_map["utr"] = f
        elif clean in ("narration", "description", "remarks", "particulars"):
            field_map["narration"] = f
        elif clean in ("currency", "curr", "ccy"):
            field_map["currency"] = f

    lines: list[ParsedStatementLine] = []
    quarantined: list[QuarantinedLine] = []

    for row_idx, row in enumerate(reader, start=2):
        raw_row_str = str(row)
        raw_amt = (
            row.get(field_map.get("amount", ""), "").strip()
            if field_map.get("amount")
            else ""
        )
        if not raw_amt:
            quarantined.append(
                QuarantinedLine(row_idx, "Missing or empty amount", raw_row_str)
            )
            continue

        try:
            amt = Decimal(raw_amt.replace(",", "").strip())
            if amt <= 0:
                quarantined.append(
                    QuarantinedLine(
                        row_idx,
                        "Amount must be strictly positive for deposit statement",
                        raw_row_str,
                    )
                )
                continue
        except (InvalidOperation, ValueError):
            quarantined.append(
                QuarantinedLine(
                    row_idx, f"Unparseable amount value '{raw_amt}'", raw_row_str
                )
            )
            continue

        raw_date = (
            row.get(field_map.get("date", ""), "") if field_map.get("date") else ""
        )
        parsed_b_date = parse_date_flexible(raw_date)
        if not parsed_b_date and raw_date:
            quarantined.append(
                QuarantinedLine(row_idx, f"Malformed date '{raw_date}'", raw_row_str)
            )
            continue

        raw_v_date = (
            row.get(field_map.get("val_date", ""), "")
            if field_map.get("val_date")
            else ""
        )
        parsed_v_date = parse_date_flexible(raw_v_date) or parsed_b_date

        utr = (
            row.get(field_map.get("utr", ""), "") if field_map.get("utr") else ""
        ).strip()
        narration = (
            row.get(field_map.get("narration", ""), "")
            if field_map.get("narration")
            else ""
        ).strip()
        currency = (
            (
                row.get(field_map.get("currency", ""), "INR")
                if field_map.get("currency")
                else "INR"
            )
            .strip()
            .upper()
        )

        if not utr and not narration:
            quarantined.append(
                QuarantinedLine(
                    row_idx, "Line has neither UTR reference nor narration", raw_row_str
                )
            )
            continue

        lines.append(
            ParsedStatementLine(
                line_number=row_idx,
                booking_date=parsed_b_date,
                value_date=parsed_v_date,
                amount=amt,
                currency=currency or "INR",
                utr=utr,
                narration=narration,
            )
        )

    return ParseResult(file_format="CSV", lines=lines, quarantined=quarantined)


def parse_statement_mt940(content: bytes) -> ParseResult:
    """Parses SWIFT MT940 statement text format."""
    text = content.decode("utf-8-sig", errors="replace")
    raw_lines = text.splitlines()

    lines: list[ParsedStatementLine] = []
    quarantined: list[QuarantinedLine] = []

    # Simple SWIFT MT940 tag parser for :61: statement line and :86: narration
    idx = 0
    while idx < len(raw_lines):
        line = raw_lines[idx].strip()
        if line.startswith(":61:"):
            # Format: :61:YYMMDD[MMDD]C/D/RC/RD[currency]amount[Ntype][ref]//[custref]
            payload = line[4:].strip()
            # Regex for tag 61: date(6) [optional value date 4] (C|D) [opt currency 1-3] amount(digits,comma)
            m = re.match(
                r"^(\d{6})(\d{4})?([A-Z]{1,2})([A-Za-z]{3})?([0-9,]+(?:\.[0-9]+)?)",
                payload,
            )
            if not m:
                quarantined.append(
                    QuarantinedLine(
                        idx + 1, "Malformed :61: MT940 statement line syntax", line
                    )
                )
                idx += 1
                continue

            val_date_str = m.group(1)
            m.group(3)
            amt_str = m.group(5).replace(",", ".")

            # Check next line for :86: narrative
            narration = ""
            utr = ""
            if idx + 1 < len(raw_lines) and raw_lines[idx + 1].startswith(":86:"):
                narration = raw_lines[idx + 1][4:].strip()
                # Extract UTR if present in narrative
                utr_match = re.search(r"\b([A-Z0-9]{12,22})\b", narration)
                if utr_match:
                    utr = utr_match.group(1)
                idx += 1

            try:
                amt = Decimal(amt_str)
            except InvalidOperation:
                quarantined.append(
                    QuarantinedLine(
                        idx + 1, f"Unparseable MT940 amount: {amt_str}", line
                    )
                )
                idx += 1
                continue

            p_date = None
            try:
                p_date = datetime.strptime(val_date_str, "%y%m%d").date()
            except ValueError:
                pass

            lines.append(
                ParsedStatementLine(
                    line_number=idx + 1,
                    booking_date=p_date,
                    value_date=p_date,
                    amount=amt,
                    currency="INR",
                    utr=utr,
                    narration=narration or payload,
                )
            )
        idx += 1

    return ParseResult(file_format="MT940", lines=lines, quarantined=quarantined)


def parse_statement_camt053(content: bytes) -> ParseResult:
    """Parses ISO 20022 CAMT.053 XML statement."""
    lines: list[ParsedStatementLine] = []
    quarantined: list[QuarantinedLine] = []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as err:
        return ParseResult(
            file_format="CAMT053",
            quarantined=[
                QuarantinedLine(
                    1,
                    f"Malformed XML in CAMT.053: {err}",
                    content[:100].decode("utf-8", "ignore"),
                )
            ],
        )

    # Strip XML namespace if present
    def strip_ns(tag: str) -> str:
        return tag.split("}")[-1] if "}" in tag else tag

    # Find all <Ntry> (entries)
    entry_idx = 1
    for elem in root.iter():
        if strip_ns(elem.tag) == "Ntry":
            raw_elem_str = ET.tostring(elem, encoding="utf-8").decode(
                "utf-8", "ignore"
            )[:200]
            amt_elem = None
            date_elem = None
            utr = ""
            narration = ""
            currency = "INR"

            for child in elem.iter():
                c_tag = strip_ns(child.tag)
                if c_tag == "Amt":
                    amt_elem = child
                    currency = child.attrib.get("Ccy", "INR")
                elif c_tag in ("BookgDt", "ValDt"):
                    for dt_child in child:
                        if strip_ns(dt_child.tag) in ("Dt", "DtTm"):
                            date_elem = dt_child.text
                elif c_tag in ("EndToEndId", "AcctSvcrRef", "TxId"):
                    if child.text and not utr:
                        utr = child.text.strip()
                elif c_tag in ("Ustrd", "AddtlNtryInf"):
                    if child.text:
                        narration = (narration + " " + child.text).strip()

            if amt_elem is None or not amt_elem.text:
                quarantined.append(
                    QuarantinedLine(
                        entry_idx, "Missing Amt in CAMT.053 entry", raw_elem_str
                    )
                )
                entry_idx += 1
                continue

            try:
                amt = Decimal(amt_elem.text.strip())
            except InvalidOperation:
                quarantined.append(
                    QuarantinedLine(
                        entry_idx,
                        f"Invalid amount format in CAMT.053: {amt_elem.text}",
                        raw_elem_str,
                    )
                )
                entry_idx += 1
                continue

            parsed_dt = parse_date_flexible(date_elem[:10]) if date_elem else None

            lines.append(
                ParsedStatementLine(
                    line_number=entry_idx,
                    booking_date=parsed_dt,
                    value_date=parsed_dt,
                    amount=amt,
                    currency=currency,
                    utr=utr,
                    narration=narration,
                )
            )
            entry_idx += 1

    return ParseResult(file_format="CAMT053", lines=lines, quarantined=quarantined)


def parse_statement(content: bytes, filename: str) -> ParseResult:
    """Dispatcher for CSV, MT940, and CAMT.053 file formats."""
    fn_lower = filename.lower()
    if fn_lower.endswith((".xml", ".camt")) or b"<Document" in content[:300]:
        return parse_statement_camt053(content)
    elif fn_lower.endswith((".sta", ".940")) or b":20:" in content[:300]:
        return parse_statement_mt940(content)
    else:
        return parse_statement_csv(content)
