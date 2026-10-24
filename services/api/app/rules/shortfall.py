"""Shortfall checker: required security deposit = sum over programmes of
(Table 1.4 base amount x intake count), x leased multiplier if the
institution's campus is leased. See config/table_1_4.yaml for the
figures-are-placeholders caveat — this module's logic is independent of
whether those figures are final.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.rules.config_loader import load_table_1_4


@dataclass
class ProgrammeIntake:
    programme_type: str  # key into table_1_4.programme_base_amounts
    intake_count: int


@dataclass
class ShortfallResult:
    required_amount: Decimal
    declared_amount: Decimal
    shortfall: Decimal  # 0 if declared >= required
    is_short: bool
    leased: bool
    breakdown: list[dict]


def compute_required_amount(
    programmes: list[ProgrammeIntake], *, leased: bool
) -> tuple[Decimal, list[dict]]:
    config = load_table_1_4()
    base_amounts = config["programme_base_amounts"]
    leased_multiplier = (
        Decimal(str(config["leased_multiplier"])) if leased else Decimal(1)
    )

    total = Decimal(0)
    breakdown = []
    for programme in programmes:
        if programme.programme_type not in base_amounts:
            raise ValueError(
                f"unknown programme type '{programme.programme_type}' — not in Table 1.4 config"
            )
        base = Decimal(str(base_amounts[programme.programme_type]))
        subtotal = base * programme.intake_count * leased_multiplier
        total += subtotal
        breakdown.append(
            {
                "programme_type": programme.programme_type,
                "intake_count": programme.intake_count,
                "base_amount": str(base),
                "leased_multiplier": str(leased_multiplier),
                "subtotal": str(subtotal),
            }
        )
    return total, breakdown


def check_shortfall(
    programmes: list[ProgrammeIntake], declared_amount: Decimal, *, leased: bool
) -> ShortfallResult:
    required, breakdown = compute_required_amount(programmes, leased=leased)
    shortfall = max(Decimal(0), required - declared_amount)
    return ShortfallResult(
        required_amount=required,
        declared_amount=declared_amount,
        shortfall=shortfall,
        is_short=shortfall > 0,
        leased=leased,
        breakdown=breakdown,
    )
