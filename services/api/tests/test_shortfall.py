from decimal import Decimal

import pytest

from app.rules.shortfall import ProgrammeIntake, check_shortfall


def test_declared_amount_covers_requirement():
    programmes = [ProgrammeIntake("DIPLOMA", 1)]
    result = check_shortfall(programmes, Decimal(1000000), leased=False)
    assert result.is_short is False
    assert result.shortfall == Decimal(0)
    assert result.required_amount == Decimal(500000)


def test_declared_amount_falls_short():
    programmes = [ProgrammeIntake("UG_DEGREE", 1)]
    result = check_shortfall(programmes, Decimal(100000), leased=False)
    assert result.is_short is True
    assert result.required_amount == Decimal(1000000)
    assert result.shortfall == Decimal(900000)


def test_leased_multiplier_doubles_requirement():
    programmes = [ProgrammeIntake("UG_DEGREE", 1)]
    owned = check_shortfall(programmes, Decimal(0), leased=False)
    leased = check_shortfall(programmes, Decimal(0), leased=True)
    assert leased.required_amount == owned.required_amount * 2


def test_multiple_programmes_sum_correctly():
    programmes = [ProgrammeIntake("DIPLOMA", 2), ProgrammeIntake("PG_DEGREE", 1)]
    result = check_shortfall(programmes, Decimal(0), leased=False)
    # 500000*2 + 1500000*1
    assert result.required_amount == Decimal(2500000)
    assert len(result.breakdown) == 2


def test_unknown_programme_type_raises():
    with pytest.raises(ValueError, match="Table 1.4"):
        check_shortfall(
            [ProgrammeIntake("NOT_A_REAL_PROGRAMME", 1)], Decimal(0), leased=False
        )
