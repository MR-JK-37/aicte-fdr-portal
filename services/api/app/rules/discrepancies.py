"""Discrepancy & Completeness Rule Engine (F-08 / SPEC §14.1 / PS Scenario "Discrepancy Identification").

Key invariants:
1. Versioned rules flag discrepancies (Discrepancy) and draft observations (ScrutinyObservation).
2. The discrepancy engine NEVER automatically rejects an instrument or labels an institution as fraudulent.
3. All discrepancies are surfaced to human officers for scrutiny and decision.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Discrepancy, Instrument
from app.models.workflow import DocumentExtraction

RULE_VERSION = "discrepancy-v1.0"
IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


@dataclass
class DiscrepancyRuleResult:
    field: str
    rule_id: str
    declared_value: str | None
    extracted_value: str | None
    severity: str  # "CRITICAL", "WARNING", "BLOCKING"
    description: str
    rule_version: str = RULE_VERSION


def check_amount_discrepancy(
    instrument: Instrument, extraction: DocumentExtraction | None
) -> DiscrepancyRuleResult | None:
    """Checks declared amount against document extraction."""
    if not extraction or not extraction.candidate_fields:
        return None

    extracted_amount_val = extraction.candidate_fields.get("amount")
    if not extracted_amount_val:
        return None

    try:
        if isinstance(extracted_amount_val, dict):
            extracted_num = Decimal(str(extracted_amount_val.get("value", 0)))
        else:
            extracted_num = Decimal(str(extracted_amount_val))
    except (ValueError, TypeError, InvalidOperation):
        return None

    declared_num = Decimal(str(instrument.amount))
    if abs(declared_num - extracted_num) > Decimal("0.01"):
        return DiscrepancyRuleResult(
            field="amount",
            rule_id="RULE_AMOUNT_MISMATCH",
            declared_value=f"₹{declared_num:,.2f}",
            extracted_value=f"₹{extracted_num:,.2f}",
            severity="CRITICAL",
            description=(
                f"Declared amount (₹{declared_num:,.2f}) does not match extracted amount "
                f"(₹{extracted_num:,.2f}) from FDR document."
            ),
        )
    return None


def check_date_discrepancy(instrument: Instrument) -> DiscrepancyRuleResult | None:
    """Checks that issue date is strictly before maturity date."""
    if (
        instrument.issue_date
        and instrument.maturity_date
        and instrument.issue_date >= instrument.maturity_date
    ):
        return DiscrepancyRuleResult(
            field="dates",
            rule_id="RULE_DATE_INCONSISTENCY",
            declared_value=f"issue={instrument.issue_date}, maturity={instrument.maturity_date}",
            extracted_value=None,
            severity="CRITICAL",
            description=(
                f"Issue date ({instrument.issue_date}) is on or after maturity date "
                f"({instrument.maturity_date}). Tenor must be positive."
            ),
        )
    return None


def check_expired_discrepancy(
    instrument: Instrument, today: date | datetime | None = None
) -> DiscrepancyRuleResult | None:
    """Flags instruments whose maturity date is already past."""
    if instrument.maturity_date is None:
        return None

    mat_date = (
        instrument.maturity_date.date()
        if isinstance(instrument.maturity_date, datetime)
        else instrument.maturity_date
    )

    comp_date = (
        today.date()
        if isinstance(today, datetime)
        else (today if today is not None else date.today())
    )

    if mat_date < comp_date:
        return DiscrepancyRuleResult(
            field="maturity_date",
            rule_id="RULE_EXPIRED_INSTRUMENT",
            declared_value=str(mat_date),
            extracted_value=None,
            severity="WARNING",
            description=(
                f"Instrument maturity date ({mat_date}) has already passed (current: {comp_date}). "
                "Renewal or replacement required."
            ),
        )
    return None


def check_ifsc_discrepancy(
    instrument: Instrument,
    extraction: DocumentExtraction | None = None,
    branch_ifsc: str | None = None,
) -> DiscrepancyRuleResult | None:
    """Validates IFSC code against the RBI 11-character format."""
    extracted_ifsc = None
    if extraction and extraction.candidate_fields:
        raw_val = extraction.candidate_fields.get("ifsc")
        if isinstance(raw_val, dict):
            extracted_ifsc = raw_val.get("value")
        elif raw_val:
            extracted_ifsc = str(raw_val)

    candidate_ifsc = branch_ifsc or extracted_ifsc
    if not candidate_ifsc:
        return None

    cleaned_ifsc = str(candidate_ifsc).strip().upper()
    if not IFSC_PATTERN.match(cleaned_ifsc):
        return DiscrepancyRuleResult(
            field="ifsc",
            rule_id="RULE_INVALID_IFSC",
            declared_value=str(candidate_ifsc),
            extracted_value=extracted_ifsc,
            severity="CRITICAL",
            description=(
                f"IFSC code '{candidate_ifsc}' is invalid. Must be 11 characters: "
                "4 alphabetic characters, followed by '0', followed by 6 alphanumeric characters."
            ),
        )
    return None


def check_duplicate_instrument_number(
    db: Session, instrument: Instrument
) -> DiscrepancyRuleResult | None:
    """Checks for existing instruments with the exact same instrument number."""
    if not instrument.instrument_number:
        return None

    cleaned_num = instrument.instrument_number.strip().upper()
    dup_stmt = select(Instrument).where(
        Instrument.id != instrument.id,
        Instrument.instrument_number == cleaned_num,
    )
    duplicate = db.execute(dup_stmt).scalars().first()
    if duplicate:
        return DiscrepancyRuleResult(
            field="instrument_number",
            rule_id="RULE_DUPLICATE_INSTRUMENT_NUMBER",
            declared_value=instrument.instrument_number,
            extracted_value=str(duplicate.id),
            severity="CRITICAL",
            description=(
                f"Instrument number '{instrument.instrument_number}' is already registered under "
                f"instrument ID {duplicate.id} (institution: {duplicate.institution_id}). "
                "Possible duplicate submission."
            ),
        )
    return None


def evaluate_all_rules(
    db: Session, instrument: Instrument, today: date | None = None
) -> list[DiscrepancyRuleResult]:
    """Evaluates all discrepancy rules against an instrument.
    NOTE: NEVER automatically rejects the instrument. Only returns identified discrepancies.
    """
    results: list[DiscrepancyRuleResult] = []

    # 1. Fetch latest document extraction if any
    ext_stmt = (
        select(DocumentExtraction)
        .where(DocumentExtraction.instrument_id == instrument.id)
        .order_by(DocumentExtraction.created_at.desc())
    )
    extraction = db.execute(ext_stmt).scalars().first()

    # 2. Run rule checks
    amt_disc = check_amount_discrepancy(instrument, extraction)
    if amt_disc:
        results.append(amt_disc)

    date_disc = check_date_discrepancy(instrument)
    if date_disc:
        results.append(date_disc)

    exp_disc = check_expired_discrepancy(instrument, today=today)
    if exp_disc:
        results.append(exp_disc)

    ifsc_disc = check_ifsc_discrepancy(instrument, extraction=extraction)
    if ifsc_disc:
        results.append(ifsc_disc)

    dup_disc = check_duplicate_instrument_number(db, instrument)
    if dup_disc:
        results.append(dup_disc)

    return results


def sync_discrepancies(
    db: Session, instrument: Instrument, today: date | None = None
) -> list[Discrepancy]:
    """Runs all discrepancy checks and upserts active Discrepancy records in the database.
    CRITICAL: Does NOT change instrument status to REJECTED.
    """
    rule_results = evaluate_all_rules(db, instrument, today=today)

    existing_discs = list(
        db.execute(
            select(Discrepancy).where(
                Discrepancy.instrument_id == instrument.id,
            )
        )
        .scalars()
        .all()
    )

    created_or_updated: list[Discrepancy] = []

    for rule_res in rule_results:
        # Match existing by field and status open
        matching = next(
            (
                d
                for d in existing_discs
                if d.field == rule_res.field and d.status in ("open", "active")
            ),
            None,
        )

        if matching:
            matching.declared_value = rule_res.declared_value
            matching.extracted_value = rule_res.extracted_value
            matching.severity = rule_res.severity
            created_or_updated.append(matching)
        else:
            new_disc = Discrepancy(
                id=uuid.uuid4(),
                institution_id=instrument.institution_id,
                instrument_id=instrument.id,
                field=rule_res.field,
                declared_value=rule_res.declared_value,
                extracted_value=rule_res.extracted_value,
                severity=rule_res.severity,
                status="open",
            )
            db.add(new_disc)
            created_or_updated.append(new_disc)

    db.flush()
    return created_or_updated
