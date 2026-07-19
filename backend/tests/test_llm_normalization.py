import asyncio
from typing import Any

import pytest

from app.intelligence.llm_normalization import (
    ProfileNormalizationError,
    structure_founder_profile,
)
from app.intelligence.profile_models import FounderProfile, Layer1Input


class FakeStructuredJsonClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.system_prompt = ""
        self.user_prompt = ""
        self.schema: dict[str, Any] = {}

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.schema = schema
        return self.response


def test_structuring_normalizes_input_and_validates_llm_output() -> None:
    output = FounderProfile().model_dump()
    output["founder"]["name"] = "Ada Lovelace"
    client = FakeStructuredJsonClient(output)
    payload = Layer1Input.model_validate(
        {"github": {"name": "  Ada   Lovelace ", "skills": ["TS"]}}
    )

    profile = asyncio.run(structure_founder_profile(payload, client))

    assert profile.founder.name == "Ada Lovelace"
    assert "TypeScript" in client.user_prompt
    assert "Never invent" in client.system_prompt
    assert client.schema["additionalProperties"] is False
    assert set(client.schema["required"]) == set(client.schema["properties"])
    _assert_all_objects_are_closed(client.schema)


def test_structuring_rejects_output_outside_founder_profile_schema() -> None:
    client = FakeStructuredJsonClient({"unexpected": True})

    with pytest.raises(ProfileNormalizationError, match="did not match"):
        asyncio.run(structure_founder_profile(Layer1Input(), client))


def _assert_all_objects_are_closed(node: Any) -> None:
    if not isinstance(node, dict):
        return
    if node.get("type") == "object":
        assert node.get("additionalProperties") is False
        for child in node.get("properties", {}).values():
            _assert_all_objects_are_closed(child)
    if isinstance(node.get("items"), dict):
        _assert_all_objects_are_closed(node["items"])
    for option in node.get("anyOf", []):
        _assert_all_objects_are_closed(option)
    for definition in node.get("$defs", {}).values():
        _assert_all_objects_are_closed(definition)