"""Business-rule validation of extracted FDR fields, run after extraction
and before the officer's L1 confirmation. Produces Discrepancy-worthy
flags, not a hard reject — officers decide what to do with a flagged file.
"""

import re
from dataclasses import dataclass

from dateutil.relativedelta import relativedelta

from app.documents.extraction import FDRExtractedFields
from app.rules.shortfall import ProgrammeIntake, check_shortfall

IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


@dataclass
class ValidationFlag:
    field: str
    severity: str  # "high" | "medium" | "low"
    message: str


def validate_extracted_fields(fields: FDRExtractedFields) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []

    if fields.ifsc and not IFSC_PATTERN.match(fields.ifsc):
        flags.append(
            ValidationFlag(
                "ifsc",
                "high",
                f"IFSC '{fields.ifsc}' does not match the standard format",
            )
        )

    if fields.issue_date and fields.maturity_date and fields.tenor_months:
        expected_maturity = fields.issue_date + relativedelta(
            months=fields.tenor_months
        )
        if expected_maturity != fields.maturity_date:
            flags.append(
                ValidationFlag(
                    "maturity_date",
                    "high",
                    f"maturity date {fields.maturity_date} does not equal issue date + tenor "
                    f"({fields.issue_date} + {fields.tenor_months}mo = {expected_maturity})",
                )
            )

    if (
        fields.issue_date
        and fields.maturity_date
        and fields.maturity_date <= fields.issue_date
    ):
        flags.append(
            ValidationFlag(
                "maturity_date", "high", "maturity date is not after the issue date"
            )
        )

    if fields.amount is not None and fields.amount_words:
        words_amount = _parse_amount_words(fields.amount_words)
        if words_amount is not None and words_amount != fields.amount:
            flags.append(
                ValidationFlag(
                    "amount",
                    "high",
                    f"amount in figures ({fields.amount}) does not match amount in words "
                    f"({fields.amount_words} = {words_amount})",
                )
            )

    if fields.amount is not None and fields.amount <= 0:
        flags.append(
            ValidationFlag("amount", "high", "declared amount must be positive")
        )

    return flags


_WORD_NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_WORD_SCALES = {
    "hundred": 100,
    "thousand": 1000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
}


def _parse_amount_words(text: str):
    """Parses Indian-English number words ("Rupees Five Lakh Only") into a
    Decimal. Best-effort: returns None (not raised) on anything it can't
    parse, since this is a cross-check signal, not a required field."""
    from decimal import Decimal

    words = re.findall(r"[a-zA-Z]+", text.lower())
    total = 0
    current = 0
    matched_any = False
    for word in words:
        if word in _WORD_NUMBERS:
            current += _WORD_NUMBERS[word]
            matched_any = True
        elif word in _WORD_SCALES:
            scale = _WORD_SCALES[word]
            if scale == 100:
                current = max(current, 1) * scale
            else:
                total += max(current, 1) * scale
                current = 0
            matched_any = True
    total += current
    return Decimal(total) if matched_any else None


def shortfall_for_submission(
    programmes: list[ProgrammeIntake], declared_amount, *, leased: bool
):
    """Thin wrapper kept here so document-pipeline callers have one import
    surface for "is this submission short against Table 1.4" alongside
    the rest of validation, delegating the actual math to app.rules."""
    return check_shortfall(programmes, declared_amount, leased=leased)
