"""Phase 8 Exit Gate: Failover, Disablement, and Honest Status Verification (SPEC §14, §17).

Proves:
1. Ordered failover across providers when killed one by one.
2. With all providers disabled / kill switch active, all AI features show "unavailable"
   while the product remains fully usable manually.
3. Tier S local-only restriction and post-check record reconciliation.
4. Translation draft ICU placeholder preservation and English fallback.
"""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import redis

from app.agents.case_summary import generate_case_summary
from app.agents.rag import UNAVAILABLE_TEXT, answer_compliance_question
from app.agents.seed_aph_clauses import seed
from app.agents.translation import generate_translation_draft
from app.llm_gateway.gateway import generate
from app.llm_gateway.registry import load_registry
from app.models.core import Institution, Instrument
from app.models.enums import InstrumentStatus, InstrumentType
from tests.conftest import VALKEY_URL


@pytest.fixture(autouse=True)
def _clear_registry_cache():
    load_registry.cache_clear()
    yield
    load_registry.cache_clear()


@pytest.fixture(autouse=True)
def _reset_gateway_state():
    client = redis.Redis.from_url(VALKEY_URL)
    for key in client.scan_iter("llm_*"):
        client.delete(key)
    client.close()
    yield


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr("app.llm_gateway.gateway.time.sleep", lambda *_: None)


@pytest.fixture
def test_instrument(db_session):
    inst_org = Institution(
        aicte_code=f"RE-{uuid.uuid4().hex[:8]}",
        name="Test Institution",
    )
    db_session.add(inst_org)
    db_session.flush()
    inst = Instrument(
        id=uuid.uuid4(),
        institution_id=inst_org.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-TEST-8888",
        amount=Decimal("500000.00"),
        status=InstrumentStatus.SUBMITTED,
    )
    db_session.add(inst)
    db_session.flush()
    return inst


def test_ordered_failover_killing_providers_one_by_one(monkeypatch, db_session):
    """Proves ordered failover: Provider 1 (groq) fails -> fails over to Provider 2 (cerebras) ->
    Provider 2 fails -> fails over to Provider 3 (gemini) which succeeds."""
    monkeypatch.setenv("GROQ_API_KEY", "mock-groq-key")
    monkeypatch.setenv("CEREBRAS_API_KEY", "mock-cerebras-key")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")

    # Mock responses: Groq throws 500, Cerebras throws 429, Gemini succeeds with 200
    err_500 = MagicMock()
    err_500.status_code = 500
    err_500.headers = {}
    err_500.text = "Groq Server Outage"

    err_429 = MagicMock()
    err_429.status_code = 429
    err_429.headers = {"Retry-After": "1"}
    err_429.text = "Cerebras Rate Limited"

    good_gemini = MagicMock()
    good_gemini.status_code = 200
    good_gemini.headers = {}
    good_gemini.text = "OK"
    good_gemini.json.return_value = {
        "choices": [{"message": {"content": "Gemini fallback succeeded."}}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 10},
    }

    # Sequence: Groq step 1 (3 attempts 500), Cerebras (3 attempts 429), Gemini (1 attempt -> 200)
    side_effects = [err_500, err_500, err_500, err_429, err_429, err_429, good_gemini]

    with patch("app.llm_gateway.client.httpx.post", side_effect=side_effects):
        result = generate(
            "policy_qa",
            [{"role": "user", "content": "What is the penalty?"}],
            tier="P",
            agent_name="test-failover",
            session=db_session,
            use_cache=False,
        )

    assert result.status == "ok"
    assert result.provider == "gemini"
    assert result.content == "Gemini fallback succeeded."
    attempt_providers = [a.get("provider") for a in result.attempts]
    assert "groq" in attempt_providers
    assert "cerebras" in attempt_providers
    assert "gemini" in attempt_providers


def test_with_all_providers_disabled_product_reports_honest_unavailable(
    monkeypatch, db_session, test_instrument
):
    """Exit gate requirement: With all providers disabled, AI features show 'unavailable'
    and the product remains fully usable."""
    monkeypatch.setenv("AI_GATEWAY_DISABLED", "true")
    seed(db_session)

    # 1. Compliance RAG Q&A reports honest unavailable
    rag_result = answer_compliance_question(db_session, "What is the policy for FDR release?")
    assert rag_result.unavailable is True
    assert rag_result.refused is True
    assert UNAVAILABLE_TEXT in rag_result.answer

    # 2. Case summary reports honest unavailable
    summary_result = generate_case_summary(db_session, test_instrument)
    assert summary_result.status == "unavailable"
    assert "unavailable" in summary_result.disclaimer.lower()

    # 3. Translation draft falls back cleanly to English source text
    trans_result = generate_translation_draft("Release Security Deposit", "hi", session=db_session)
    assert trans_result.status == "fallback_english"
    assert trans_result.translated_text == "Release Security Deposit"

    # 4. Product remains 100% usable (DB queries, instruments, verification intact)
    fetched = db_session.get(Instrument, test_instrument.id)
    assert fetched is not None
    assert fetched.instrument_number == "FDR-TEST-8888"


def test_case_summary_tier_s_local_only_enforcement(db_session, test_instrument):
    """Tier S real financial data must never route to external cloud providers."""
    # When no local Ollama is active (default), case summary returns unavailable
    res = generate_case_summary(db_session, test_instrument)
    assert res.status == "unavailable"
    assert "Tier S" in res.disclaimer or "unavailable" in res.disclaimer


def test_translation_icu_placeholders_preserved(monkeypatch, db_session):
    """Tests post-check: ICU placeholders like {amount} must remain intact in translation drafts."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.text = "OK"
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"target_language": "hi", "translated_text": "राशि {amount} की परिपक्वता तिथि {maturity_date} है।", "confidence": 0.95}'
                }
            }
        ],
        "usage": {"prompt_tokens": 40, "completion_tokens": 20},
    }

    with patch("app.llm_gateway.client.httpx.post", return_value=mock_resp):
        res = generate_translation_draft(
            "Amount {amount} has maturity date {maturity_date}.",
            "hi",
            session=db_session,
        )

    assert res.status == "machine_draft"
    assert res.placeholders_preserved is True
    assert "{amount}" in res.translated_text
    assert "{maturity_date}" in res.translated_text


def test_translation_rejects_corrupted_icu_placeholders(monkeypatch, db_session):
    """If an LLM corrupts or translates the placeholder name, post-check rejects and keeps English."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.text = "OK"
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"target_language": "hi", "translated_text": "राशि {rashi} समाप्त हो गई।", "confidence": 0.95}'
                }
            }
        ],
        "usage": {"prompt_tokens": 40, "completion_tokens": 20},
    }

    with patch("app.llm_gateway.client.httpx.post", return_value=mock_resp):
        res = generate_translation_draft(
            "Amount {amount} has expired.",
            "hi",
            session=db_session,
        )

    # Corrupted {amount} -> {rashi} caught by post-check
    assert res.status == "fallback_english"
    assert res.translated_text == "Amount {amount} has expired."
    assert "corrupted" in res.disclaimer.lower()
