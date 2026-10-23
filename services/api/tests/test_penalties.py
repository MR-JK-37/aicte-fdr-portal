from decimal import Decimal

import pytest

from app.rules.penalties import calculate_penalty


def test_band_0_days_applies_lowest_rate():
    result = calculate_penalty(Decimal(100000), days_overdue=0)
    assert result.band_min_days == 0
    assert result.rate == Decimal("0.10")
    assert result.penalty_amount == Decimal("10000.00")


def test_band_30_days_applies_middle_rate():
    result = calculate_penalty(Decimal(100000), days_overdue=45)
    assert result.band_min_days == 30
    assert result.rate == Decimal("0.20")
    assert result.penalty_amount == Decimal("20000.00")


def test_band_90_days_applies_highest_rate():
    result = calculate_penalty(Decimal(100000), days_overdue=120)
    assert result.band_min_days == 90
    assert result.rate == Decimal("0.50")
    assert result.penalty_amount == Decimal("50000.00")


def test_exact_band_boundary_uses_new_band():
    result = calculate_penalty(Decimal(100000), days_overdue=30)
    assert result.band_min_days == 30


def test_negative_days_overdue_rejected():
    with pytest.raises(ValueError):
        calculate_penalty(Decimal(100000), days_overdue=-1)


def test_conflict_is_always_flagged_given_current_config():
    # Per config/penalties.yaml: the APH penalty rate is an unresolved
    # open question, so every result must carry this flag until AICTE
    # confirms a rate and the config is updated.
    result = calculate_penalty(Decimal(1), days_overdue=0)
    assert result.conflict_flagged is True
