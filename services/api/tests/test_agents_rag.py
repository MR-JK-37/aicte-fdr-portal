from unittest.mock import MagicMock, patch

import pytest

from app.agents.rag import REFUSAL_TEXT, answer_compliance_question, retrieve
from app.agents.seed_aph_clauses import seed


@pytest.fixture(autouse=True)
def _groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-for-rag-tests")


@pytest.fixture
def seeded(db_session):
    seed(db_session)
    db_session.flush()
    return db_session


def test_retrieve_finds_the_relevant_clause(seeded):
    results = retrieve(
        seeded, "release of security deposit clearance NOC sanction order", top_k=1
    )
    assert results[0].clause_id == "APH 2024-27, cl. 6.46"


def test_retrieve_marks_synthetic_clauses_as_synthetic(seeded):
    results = retrieve(seeded, "joint account creation and lien marking", top_k=1)
    assert results[0].clause_id == "APH 2024-27, cl. 6.08"
    assert results[0].synthetic_placeholder is True


def test_retrieve_marks_source_indexed_clauses_as_not_synthetic(seeded):
    results = retrieve(
        seeded,
        "Engineering Technology Undergraduate Management BBA MCA deposit amount lakh programme",
        top_k=1,
    )
    assert results[0].clause_id == "APH 2024-27, cl. 1.12 / Table 1.4"
    assert results[0].synthetic_placeholder is False


def test_answer_refuses_for_an_unrelated_question(seeded):
    answer = answer_compliance_question(seeded, "what is the capital of France")
    assert answer.refused is True
    assert answer.answer == REFUSAL_TEXT


def test_answer_calls_llm_with_retrieved_context_when_confident(seeded):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Per [APH 2024-27, cl. 6.46]: requires Affidavit 6, the FDR/RTGS release path, and resolved clearances."
                }
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20},
    }
    with patch(
        "app.llm_gateway.client.httpx.post", return_value=mock_response
    ) as mock_post:
        answer = answer_compliance_question(
            seeded, "release of security deposit clearance NOC sanction order"
        )
    assert mock_post.call_count == 1
    assert answer.refused is False
    assert "6.46" in answer.answer


def test_answer_tags_synthetic_context_for_the_llm(seeded):
    """Synthetic-only retrievals must still reach the LLM prompt tagged
    `[SYNTHETIC PLACEHOLDER]`, so a real provider can't present invented
    clause text as AICTE policy without at least seeing the disclaimer."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Per [APH 2024-27, cl. 6.08]: joint names with the Regional Officer, AICTE, with a marked lien."
                }
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20},
    }
    with patch(
        "app.llm_gateway.client.httpx.post", return_value=mock_response
    ) as mock_post:
        answer_compliance_question(seeded, "joint account creation and lien marking")

    sent_payload = mock_post.call_args.kwargs["json"]
    sent_text = str(sent_payload["messages"])
    assert "SYNTHETIC" in sent_text or "synthetic" in sent_text.lower()
