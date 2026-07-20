"""Layer 3 founder intelligence enrichment."""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings
from app.intelligence.llm_normalization import (
    OpenAIProfileClient,
    StructuredJsonClient,
    _strict_json_schema,
)
from app.intelligence.profile_models import FounderIntelligence, FounderProfile

FOUNDER_INTELLIGENCE_SYSTEM_PROMPT = """You are the Founder Intelligence Engine.

Enrich the supplied structured FounderProfile using only its source-backed
facts and evidence. Return JSON matching the FounderIntelligence schema.

Rules:
- Do not rewrite or replace the FounderProfile.
- Do not infer from gender, ethnicity, age, nationality, university prestige,
  social network, location, name, or other demographic proxies.
- Do not make an investment recommendation or assign an investment score.
- Every insight must have a matching reasoning entry and evidenceReferences
  entry. Use an empty evidence list when the available profile has no support.
- Represent missing or uncertain information in missingInformation.
- Keep confidence scores between 0 and 1.
- Limited public software is not a weakness for research founders when
  published technical work is present.
- Return JSON only.
"""


class FounderIntelligenceError(ValueError):
    """Raised when the intelligence provider returns an invalid result."""


class FounderIntelligenceService:
    """Generate Layer 3 intelligence without changing Layer 2 source data."""

    def __init__(self, client: StructuredJsonClient):
        self._client = client

    async def enrich(self, profile: FounderProfile) -> FounderIntelligence:
        try:
            response = await self._client.complete_json(
                system_prompt=FOUNDER_INTELLIGENCE_SYSTEM_PROMPT,
                user_prompt=build_founder_intelligence_prompt(profile),
                schema=_strict_json_schema(FounderIntelligence.model_json_schema()),
            )
            return FounderIntelligence.model_validate(response)
        except (ValidationError, ValueError) as error:
            raise FounderIntelligenceError(
                "The LLM response did not match the FounderIntelligence schema."
            ) from error
        except Exception as error:
            raise FounderIntelligenceError(
                "Founder intelligence generation failed."
            ) from error


def build_founder_intelligence_prompt(profile: FounderProfile) -> str:
    """Serialize the validated profile deterministically for the provider."""

    return json.dumps(
        profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def build_founder_intelligence_service(
    settings: Settings | None = None,
) -> FounderIntelligenceService:
    settings = settings or get_settings()
    if not settings.openai_api_key:
        raise IntegrationNotConfigured(
            "Founder intelligence requires OPENAI_API_KEY."
        )
    return FounderIntelligenceService(
        OpenAIProfileClient(api_key=settings.openai_api_key.get_secret_value())
    )