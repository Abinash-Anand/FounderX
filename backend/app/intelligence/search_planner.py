"""OpenAI-backed planning of focused VC web searches."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from pydantic import BaseModel, Field, ValidationError

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)

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
        }
    },
    "required": ["searches"],
    "additionalProperties": False,
}


class SearchPlan(BaseModel):
    searches: list[str] = Field(min_length=1, max_length=10)


class SearchPlanningError(ValueError):
    """Raised when search planning cannot produce a valid plan."""


def _log_openai_request_error(error: Exception, model: str) -> None:
    logger.exception(
        "OpenAI search-planning request failed: class=%s status_code=%s code=%s "
        "message=%s model=%s",
        type(error).__name__,
        getattr(error, "status_code", None),
        getattr(error, "code", None),
        str(error),
        model,
        exc_info=error,
    )


class SearchPlanner:
    """Generate focused search queries using OpenAI structured output."""

    def __init__(
        self,
        client: Any,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._api_key = api_key

    async def plan(self, query: str) -> SearchPlan:
        query = query.strip()
        if not query:
            raise SearchPlanningError("The VC query must not be empty.")

        try:
            logger.info(
                "OpenAI search-planning request: model=%s OPENAI_API_KEY loaded=%s "
                "prefix=%s length=%d",
                self._model,
                bool(self._api_key),
                self._api_key[:8] if self._api_key else "",
                len(self._api_key or ""),
            )
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
        except (
            AuthenticationError,
            RateLimitError,
            BadRequestError,
            APIConnectionError,
            APIStatusError,
        ) as error:
            _log_openai_request_error(error, self._model)
            raise SearchPlanningError("The search planning request failed.") from error
        except Exception as error:  # Do not expose provider details or credentials.
            logger.exception(
                "OpenAI search-planning request failed: class=%s message=%s model=%s",
                type(error).__name__,
                str(error),
                self._model,
                exc_info=error,
            )
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
    api_key = settings.openai_api_key.get_secret_value()
    return SearchPlanner(AsyncOpenAI(api_key=api_key), api_key=api_key)
