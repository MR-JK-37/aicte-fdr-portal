from pydantic import BaseModel

from app.llm_gateway.schema_validation import (
    build_repair_prompt,
    validate_json_response,
)


class Toy(BaseModel):
    name: str
    amount: int


def test_valid_json_matching_schema():
    result = validate_json_response('{"name": "x", "amount": 5}', Toy)
    assert result.ok is True
    assert result.parsed.name == "x"
    assert result.parsed.amount == 5


def test_not_json_at_all():
    result = validate_json_response("this is not json", Toy)
    assert result.ok is False
    assert "not valid JSON" in result.error


def test_json_but_wrong_schema():
    result = validate_json_response('{"name": "x"}', Toy)  # missing "amount"
    assert result.ok is False
    assert result.parsed is None


def test_build_repair_prompt_includes_error_and_schema():
    original = [{"role": "user", "content": "extract fields"}]
    repair = build_repair_prompt(original, "bad output", "amount missing", Toy)
    assert repair[0] == original[0]
    assert repair[-1]["role"] == "user"
    assert "amount missing" in repair[-1]["content"]
    assert "bad output" in repair[-2]["content"]
