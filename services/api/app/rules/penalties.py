"""Penalty calculator, config-driven per config/penalties.yaml. Always
reports conflict_flagged from that file so callers (API responses, UI) can
show a banner rather than presenting a guessed rate as authoritative — see
that file's header for why.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.rules.config_loader import load_penalty_config


@dataclass
class PenaltyResult:
    amount_base: Decimal
    days_overdue: int
    rate: Decimal
    penalty_amount: Decimal
    conflict_flagged: bool
    band_min_days: int


def _select_band(bands: list[dict], days_overdue: int) -> dict:
    # Bands are ascending by min_days_overdue; pick the highest band whose
    # threshold the overdue duration has crossed.
    applicable = [b for b in bands if days_overdue >= b["min_days_overdue"]]
    if not applicable:
        raise ValueError("no penalty band matches a negative days_overdue")
    return max(applicable, key=lambda b: b["min_days_overdue"])


def calculate_penalty(amount_base: Decimal, days_overdue: int) -> PenaltyResult:
    if days_overdue < 0:
        raise ValueError("days_overdue must be >= 0")
    config = load_penalty_config()
    band = _select_band(config["bands"], days_overdue)
    rate = Decimal(str(band["rate"]))
    penalty_amount = (amount_base * rate).quantize(Decimal("0.01"))
    return PenaltyResult(
        amount_base=amount_base,
        days_overdue=days_overdue,
        rate=rate,
        penalty_amount=penalty_amount,
        conflict_flagged=bool(config.get("conflict_flagged", False)),
        band_min_days=band["min_days_overdue"],
    )
