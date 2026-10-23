"""SIMULATED SFMS/NeSL-style feed for bank guarantee instruments
(BG/E_BG/SURETY_BOND). Real integration ownership is an open question
(Blueprint.txt §17 item 3); this simulates the shape of a periodic feed
message confirming or revoking a guarantee, for the verification
workflow to consume — not a real connection to SFMS or NeSL.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class SfmsFeedRecord:
    simulated: bool
    instrument_number: str
    status: str  # "ACTIVE" | "INVOKED" | "EXPIRED" | "NOT_FOUND"
    as_of: datetime


def fetch_feed_record(instrument_number: str, *, rng: random.Random | None = None) -> SfmsFeedRecord:
    rng = rng or random.Random()
    status = rng.choices(
        ["ACTIVE", "INVOKED", "EXPIRED", "NOT_FOUND"],
        weights=[0.85, 0.03, 0.07, 0.05],
        k=1,
    )[0]
    return SfmsFeedRecord(
        simulated=True,
        instrument_number=instrument_number,
        status=status,
        as_of=datetime.now(UTC),
    )
