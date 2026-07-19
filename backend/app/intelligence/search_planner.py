"""OpenAI-backed planning of focused VC web searches."""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings

SEARCH_PLANNER_SYSTEM_PROMPT = """You are a search planning agent.

Your job is to convert a VC's natural language query into one or more web searches.

Rules:
- Break large queries into smaller focused searches.
- Each search should answer one question.
- Avoid combining unrelated objectives.
- Prefer searches that identify companies before founders.
- Search for founder biographies separately.
- Search for funding separately if necessary.
- Search for conference talks separately if necessary.

Return only this JSON shape:
{
  "searches": ["...", "..."]
}
"""

SEARCH_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "searches": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 10,
        }
    },
    "required": ["searches"],
    "additionalProperties": False,
}


class SearchPlan(BaseModel):
    searches: list[str] = Field(min_length=1, max_length=10)


class SearchPlanningError(ValueError):
    """Raised when search planning cannot produce a valid plan."""


class SearchPlanner:
    """Generate focused search queries using OpenAI structured output."""

    def __init__(self, client: Any, *, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    async def plan(self, query: str) -> SearchPlan:
        query = query.strip()
        if not query:
            raise SearchPlanningError("The VC query must not be empty.")

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SEARCH_PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "SearchPlan",
                        "strict": True,
                        "schema": SEARCH_PLAN_SCHEMA,
                    },
                },
            )
        except Exception as error:  # Do not expose provider details or credentials.
            raise SearchPlanningError("The search planning request failed.") from error

        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise SearchPlanningError("The search planner returned an empty response.")
        try:
            return SearchPlan.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError, TypeError) as error:
            raise SearchPlanningError("The search planner returned an invalid plan.") from error


def build_search_planner(settings: Settings | None = None) -> SearchPlanner:
    settings = settings or get_settings()
    if not settings.openai_api_key:
        raise IntegrationNotConfigured("Search planning requires OPENAI_API_KEY.")
    return SearchPlanner(AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value()))
