"""SIMULATED bank-confirmation API.

Real bank confirmation channels for FDRs/BGs in production require a
licensed integration with each bank (SFMS/NeSL/e-BG-style channels, email,
or portal — Blueprint.txt §17 item 3 lists this as unresolved: "who owns
those integrations?"). This module is a deterministic, clearly-labelled
simulation standing in for that integration: it signs its own responses
with an HMAC so the signature-verification code path is real and
testable, but the "bank" on the other end does not exist.

Every response carries `"simulated": True` so no caller can mistake it
for a real confirmation — and nothing in this module is wired to a real
bank endpoint anywhere.
"""

import hashlib
import hmac
import json
import random
import time
from dataclasses import dataclass
from decimal import Decimal

# Dev-only HMAC key for simulating a signed bank response. Never a real
# bank's key — this entire module is simulated.
_SIGNING_KEY = b"SIMULATED-BANK-CONFIRMATION-KEY-DO-NOT-USE-IN-PRODUCTION"


@dataclass
class BankConfirmationResponse:
    simulated: bool
    confirmed: bool
    confirmed_amount: Decimal | None
    bank_reference: str
    latency_ms: int
    signature: str
    payload: dict


def _sign(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(_SIGNING_KEY, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(payload: dict, signature: str) -> bool:
    return hmac.compare_digest(_sign(payload), signature)


def request_confirmation(
    instrument_number: str,
    ifsc: str | None,
    declared_amount: Decimal,
    *,
    failure_rate: float = 0.1,
    min_latency_ms: int = 50,
    max_latency_ms: int = 400,
    rng: random.Random | None = None,
) -> BankConfirmationResponse:
    """Simulates a signed bank-confirmation reply. `rng` is injectable so
    tests can make outcomes deterministic without disabling the
    latency/failure simulation entirely."""
    rng = rng or random.Random()
    latency_ms = rng.randint(min_latency_ms, max_latency_ms)
    time.sleep(latency_ms / 1000)

    if rng.random() < failure_rate:
        payload = {
            "instrument_number": instrument_number,
            "ifsc": ifsc,
            "confirmed": False,
            "confirmed_amount": None,
            "bank_reference": None,
            "reason": "SIMULATED: bank system timeout",
        }
        return BankConfirmationResponse(
            simulated=True,
            confirmed=False,
            confirmed_amount=None,
            bank_reference="",
            latency_ms=latency_ms,
            signature=_sign(payload),
            payload=payload,
        )

    # Simulated confirmation: agrees with the declared amount in the
    # common case, with a small chance of a discrepancy to exercise the
    # declared-vs-confirmed diff path.
    confirmed_amount = declared_amount
    if rng.random() < 0.05:
        confirmed_amount = declared_amount * Decimal(str(rng.choice([0.9, 0.95, 1.05])))

    bank_reference = f"SIMBANK-{rng.randint(100000, 999999)}"
    payload = {
        "instrument_number": instrument_number,
        "ifsc": ifsc,
        "confirmed": True,
        "confirmed_amount": str(confirmed_amount),
        "bank_reference": bank_reference,
    }
    return BankConfirmationResponse(
        simulated=True,
        confirmed=True,
        confirmed_amount=confirmed_amount,
        bank_reference=bank_reference,
        latency_ms=latency_ms,
        signature=_sign(payload),
        payload=payload,
    )
