from unittest.mock import MagicMock, patch

import pytest

from app.agents.forgery_explain import explain_flags
from app.documents.forgery import ForgerySignal
from app.documents.validation import ValidationFlag


@pytest.fixture(autouse=True)
def _groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-for-explain-tests")


def test_no_flags_short_circuits_without_calling_llm(db_session):
    with patch("app.llm_gateway.client.httpx.post") as mock_post:
        explanation = explain_flags(db_session, [], [])
    mock_post.assert_not_called()
    assert "no flags" in explanation.lower()


def test_flags_are_sent_to_llm_and_explanation_returned(db_session):
    flags = [ValidationFlag("ifsc", "high", "IFSC format invalid")]
    signals = [ForgerySignal("duplicate_phash", "high", "matches another document")]
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This document has two issues to check: an invalid IFSC and a duplicate image."
                }
            }
        ],
        "usage": {"prompt_tokens": 40, "completion_tokens": 15},
    }
    with patch(
        "app.llm_gateway.client.httpx.post", return_value=mock_response
    ) as mock_post:
        explanation = explain_flags(db_session, flags, signals)
    assert mock_post.call_count == 1
    assert "invalid IFSC" in explanation or "issues" in explanation

    sent = str(mock_post.call_args.kwargs["json"]["messages"])
    assert "IFSC format invalid" in sent
    assert "matches another document" in sent


def test_falls_back_to_raw_flags_when_llm_unavailable(db_session, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    flags = [ValidationFlag("amount", "high", "amount mismatch")]
    explanation = explain_flags(db_session, flags, [])
    assert "amount mismatch" in explanation
