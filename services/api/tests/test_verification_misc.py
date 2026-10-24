from decimal import Decimal

from app.models.enums import EvidenceLevel
from app.verification.badges import BADGES, badge_for
from app.verification.diff import build_declared_vs_confirmed_diff


def test_diff_with_no_confirmation_yet():
    rows = build_declared_vs_confirmed_diff(
        declared_amount=Decimal(500000), confirmed_amount=None, source=None
    )
    assert rows[0].confirmed is None
    assert rows[0].matches is None


def test_diff_matching_amounts():
    rows = build_declared_vs_confirmed_diff(
        declared_amount=Decimal(500000),
        confirmed_amount=Decimal(500000),
        source="bank_verifier_reply",
    )
    amount_row = next(r for r in rows if r.field == "amount")
    assert amount_row.matches is True


def test_diff_mismatched_amounts():
    rows = build_declared_vs_confirmed_diff(
        declared_amount=Decimal(500000),
        confirmed_amount=Decimal(450000),
        source="bank_verifier_reply",
    )
    amount_row = next(r for r in rows if r.field == "amount")
    assert amount_row.matches is False


def test_every_evidence_level_has_a_badge():
    for level in EvidenceLevel:
        assert level in BADGES
        badge = badge_for(level)
        assert "label" in badge and "icon" in badge and "tone" in badge
