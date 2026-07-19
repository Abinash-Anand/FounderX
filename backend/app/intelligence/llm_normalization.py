"""LLM-backed structuring from normalized Layer 1 data to FounderProfile."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Protocol, cast

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.intelligence.normalization import normalize_founder_payload
from app.intelligence.profile_models import FounderProfile, Layer1Input

FOUNDER_PROFILE_SYSTEM_PROMPT = """You are a Founder Data Structuring Engine.

Convert the supplied, source-backed founder data into the FounderProfile schema.
Follow the schema exactly and return JSON only.

Rules:
- Never invent, infer, or hallucinate founder information.
- Use only facts present in the supplied source payload.
- Use empty strings, empty arrays, zero, or false when the schema requires a
  value but the source does not provide one.
- Record important missing or uncertain information in `unknowns`.
- Put each source-backed evidence object in the top-level `evidence` registry
    exactly once and reference it from entities with `evidenceIds`.
- Preserve source URLs and supporting evidence whenever they are available.
- If sources disagree, preserve both claims with their separate evidence and
  record the conflict in `unknowns`; never silently choose a winner.
- Do not score the founder or make an investment recommendation.
"""


class StructuredJsonClient(Protocol):
    """Provider interface used by the structuring stage and its tests."""

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]: ...


class ProfileNormalizationError(ValueError):
    """Raised when the LLM cannot produce a valid FounderProfile."""


class OpenAIProfileClient:
    """OpenAI adapter using strict JSON-schema chat completions."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        response: Any = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "FounderProfile",
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        content = response.choices[0].message.content
        if not content:
            raise ProfileNormalizationError("The LLM returned an empty response.")
        try:
            result = json.loads(content)
        except json.JSONDecodeError as error:
            raise ProfileNormalizationError("The LLM returned invalid JSON.") from error
        if not isinstance(result, dict):
            raise ProfileNormalizationError("The LLM response must be a JSON object.")
        return cast(dict[str, Any], result)


def build_founder_structuring_prompt(payload: Layer1Input) -> str:
    """Build the user prompt from the already validated Layer 1 contract."""
    normalized_payload = normalize_founder_payload(payload.model_dump(mode="python"))
    return json.dumps(normalized_payload, indent=2, ensure_ascii=False, sort_keys=True)


def _visit_schema_node(node: Any) -> None:
    if not isinstance(node, dict):
        return

    node_dict = cast(dict[str, Any], node)
    node_type = node_dict.get("type")

    if node_type == "object":
        _apply_object_schema(node_dict)
    elif node_type == "array":
        _apply_array_schema(node_dict)

    _visit_schema_definitions(node_dict)


def _apply_object_schema(node_dict: dict[str, Any]) -> None:
    properties = node_dict.get("properties")
    if not isinstance(properties, dict):
        return

    properties_dict = cast(dict[str, Any], properties)
    node_dict["additionalProperties"] = False
    node_dict["required"] = list(properties_dict.keys())
    for child in properties_dict.values():
        _visit_schema_node(child)


def _apply_array_schema(node_dict: dict[str, Any]) -> None:
    items = node_dict.get("items")
    if isinstance(items, dict):
        _visit_schema_node(items)


def _visit_schema_definitions(node_dict: dict[str, Any]) -> None:
    definitions = node_dict.get("$defs")
    if isinstance(definitions, dict):
        for definition in cast(dict[str, Any], definitions).values():
            _visit_schema_node(definition)


def _strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Make Pydantic's schema compatible with OpenAI strict structured outputs."""
    strict_schema = deepcopy(schema)
    _visit_schema_node(strict_schema)
    return strict_schema


async def structure_founder_profile(
    payload: Layer1Input,
    client: StructuredJsonClient,
) -> FounderProfile:
    """Normalize source data, ask the LLM to structure it, then validate output."""
    user_prompt = build_founder_structuring_prompt(payload)
    response = await client.complete_json(
        system_prompt=FOUNDER_PROFILE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=_strict_json_schema(FounderProfile.model_json_schema()),
    )
    try:
        return FounderProfile.model_validate(response)
    except (ValidationError, ValueError) as error:
        raise ProfileNormalizationError(
            "The LLM response did not match the FounderProfile schema."
        ) from error