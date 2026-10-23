import random
from decimal import Decimal

from app.verification.mock_bank_api import request_confirmation, verify_signature


def test_response_is_marked_simulated():
    response = request_confirmation(
        "FDR1", "SBIN0001234", Decimal(500000), rng=random.Random(1), min_latency_ms=0, max_latency_ms=1
    )
    assert response.simulated is True


def test_signature_verifies_against_untampered_payload():
    response = request_confirmation(
        "FDR1", "SBIN0001234", Decimal(500000), rng=random.Random(1), min_latency_ms=0, max_latency_ms=1
    )
    assert verify_signature(response.payload, response.signature) is True


def test_signature_fails_if_payload_tampered():
    response = request_confirmation(
        "FDR1", "SBIN0001234", Decimal(500000), rng=random.Random(1), min_latency_ms=0, max_latency_ms=1
    )
    tampered = dict(response.payload)
    tampered["confirmed_amount"] = "999999999"
    assert verify_signature(tampered, response.signature) is False


def test_failure_rate_zero_always_confirms():
    response = request_confirmation(
        "FDR1", None, Decimal(500000), failure_rate=0.0, rng=random.Random(5), min_latency_ms=0, max_latency_ms=1
    )
    assert response.confirmed is True


def test_failure_rate_one_always_fails():
    response = request_confirmation(
        "FDR1", None, Decimal(500000), failure_rate=1.0, rng=random.Random(5), min_latency_ms=0, max_latency_ms=1
    )
    assert response.confirmed is False
    assert response.confirmed_amount is None
