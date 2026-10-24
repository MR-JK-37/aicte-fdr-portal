"""JSON-schema validation of LLM output against a Pydantic model, with
the repair-prompt text the gateway uses for its one-retry-then-
cross-provider-reask policy (see gateway.py).
"""

import json

from pydantic import BaseModel, ValidationError


class SchemaValidationResult:
    def __init__(self, ok: bool, parsed: BaseModel | None, error: str | None):
        self.ok = ok
        self.parsed = parsed
        self.error = error


def validate_json_response(
    raw_content: str, schema: type[BaseModel]
) -> SchemaValidationResult:
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        return SchemaValidationResult(False, None, f"not valid JSON: {exc}")
    try:
        parsed = schema.model_validate(data)
    except ValidationError as exc:
        return SchemaValidationResult(False, None, str(exc))
    return SchemaValidationResult(True, parsed, None)


def build_repair_prompt(
    original_messages: list[dict], bad_output: str, error: str, schema: type[BaseModel]
) -> list[dict]:
    schema_json = json.dumps(schema.model_json_schema())
    repair_instruction = (
        "Your previous response did not match the required JSON schema.\n"
        f"Error: {error}\n"
        f"Required JSON schema: {schema_json}\n"
        f"Your previous output was: {bad_output}\n"
        "Reply with ONLY valid JSON matching the schema, no other text."
    )
    return [
        *original_messages,
        {"role": "assistant", "content": bad_output},
        {"role": "user", "content": repair_instruction},
    ]
