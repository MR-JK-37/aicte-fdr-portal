from unittest.mock import MagicMock, patch

import pytest

from app.agents.document_intelligence import LLMGatewayExtractor
from app.documents.extraction import FDRExtractedFields


@pytest.fixture(autouse=True)
def _groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-for-di-tests")


def _mock_response(json_body):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_body
    return resp


def test_extract_returns_parsed_fields_from_llm():
    body = {
        "choices": [
            {
                "message": {
                    "content": '{"instrument_number": "FDR123456", "amount": "500000"}'
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20},
    }
    extractor = LLMGatewayExtractor()
    with patch(
        "app.llm_gateway.client.httpx.post", return_value=_mock_response(body)
    ) as mock_post:
        fields = extractor.extract("FDR No: FDR123456. Amount: Rs. 500000.")
    assert mock_post.call_count == 1
    assert isinstance(fields, FDRExtractedFields)
    assert fields.instrument_number == "FDR123456"


def test_extract_sends_the_ocr_text_in_the_prompt():
    body = {"choices": [{"message": {"content": "{}"}}], "usage": {}}
    extractor = LLMGatewayExtractor()
    with patch(
        "app.llm_gateway.client.httpx.post", return_value=_mock_response(body)
    ) as mock_post:
        extractor.extract("UNIQUE_MARKER_TEXT_12345")
    sent = str(mock_post.call_args.kwargs["json"]["messages"])
    assert "UNIQUE_MARKER_TEXT_12345" in sent


def test_extract_falls_back_to_empty_fields_on_gateway_failure(monkeypatch):
    monkeypatch.delenv(
        "GROQ_API_KEY", raising=False
    )  # no provider keyed -> human_review_required
    extractor = LLMGatewayExtractor()
    fields = extractor.extract("some text")
    assert fields == FDRExtractedFields()


def test_extract_logs_to_agent_runs_when_session_given(db_session):
    from sqlalchemy import select

    from app.models.audit import AgentRun

    body = {
        "choices": [{"message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 1},
    }
    extractor = LLMGatewayExtractor(session=db_session, agent_name="test-doc-intel")
    with patch("app.llm_gateway.client.httpx.post", return_value=_mock_response(body)):
        extractor.extract("some fdr text")
    run = (
        db_session.execute(
            select(AgentRun).where(AgentRun.agent_name == "test-doc-intel")
        )
        .scalars()
        .first()
    )
    assert run is not None
    assert run.task_class == "extraction"
