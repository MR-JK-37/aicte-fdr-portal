"""Declared-vs-confirmed diff, per the brief's acceptance criterion
("declared-vs-confirmed diff view; evidence badges everywhere"). This is
the data shape the web UI (Phase 9) renders as a side-by-side view; no UI
exists yet, so this is the API-shaped contract for it.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class DiffField:
    field: str
    declared: str
    confirmed: str | None
    matches: bool | None  # None when there's nothing to confirm against yet


def build_declared_vs_confirmed_diff(
    *, declared_amount: Decimal, confirmed_amount: Decimal | None, source: str | None
) -> list[DiffField]:
    if confirmed_amount is None:
        return [DiffField("amount", str(declared_amount), None, None)]
    matches = abs(declared_amount - confirmed_amount) <= Decimal("0.01")
    return [
        DiffField("amount", str(declared_amount), str(confirmed_amount), matches),
        DiffField("source", "institution-declared", source or "unknown", None),
    ]
