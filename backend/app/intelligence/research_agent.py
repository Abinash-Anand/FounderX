"""Tool-using VC research agent that produces a Layer 1 hand-off payload."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings
from app.integrations.tavily.search import TavilySearch, build_tavily_search
from app.intelligence.founder_extraction import (
    FounderExtractionError,
    FounderIntelligenceExtractionAgent,
)
from app.intelligence.profile_models import Layer1Input
from app.intelligence.search_planner import SearchPlanner, SearchPlanningError

VC_RESEARCH_SYSTEM_PROMPT = """You are an AI Venture Capital Research Agent.

Your goal is to identify startup founders that satisfy a VC's investment query.

You have access to one tool:

- Tavily Search

Whenever you do not have enough information, use Tavily Search to gather
additional evidence. You may perform multiple searches before answering.

Guidelines:
1. Break complex VC queries into smaller search tasks.
2. Search for startups first.
3. Identify founders.
4. Collect founder information.
5. Verify claims whenever possible.
6. Prefer recent and reliable sources.
7. Never hallucinate founder information.
8. If information cannot be verified, use "Unknown".

When you have enough evidence, return only a JSON object with this shape:
{
  "github": {},
  "resume": {},
  "website": {},
  "tavily": {},
  "metadata": {
    "founderId": "",
    "collectedAt": "",
    "dataSources": ["tavily"]
  }
}

Put search-backed findings and their source URLs under `tavily`. Keep the
source payload evidence-oriented. Do not explain your reasoning outside the
JSON object.
"""

TAVILY_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "tavily_search",
        "description": "Search the web for recent, reliable startup and founder evidence.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A focused web search query.",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


class ResearchAgentError(ValueError):
    """Raised when the research agent cannot produce a valid Layer 1 payload."""


class ResearchChatClient(Protocol):
    """Minimal chat-completions interface for provider-independent testing."""

    @property
    def chat(self) -> Any: ...


class VCResearchAgent:
    """Run an OpenAI tool loop with Tavily and return validated Layer 1 data."""

    def __init__(
        self,
        client: Any,
        tavily: TavilySearch,
        *,
        extractor: FounderIntelligenceExtractionAgent | None = None,
        planner: SearchPlanner | None = None,
        model: str = "gpt-4o-mini",
        max_rounds: int = 6,
    ) -> None:
        self._client = client
        self._tavily = tavily
        self._extractor = extractor
        self._planner = planner
        self._model = model
        self._max_rounds = max_rounds

    async def research(self, query: str) -> Layer1Input:
        """Research a VC query, allowing the model to issue multiple searches."""
        query = query.strip()
        if not query:
            raise ResearchAgentError("The VC query must not be empty.")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": VC_RESEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        searches: list[dict[str, Any]] = []
        if self._planner:
            try:
                plan = await self._planner.plan(query)
            except SearchPlanningError as error:
                raise ResearchAgentError("The search planning step failed.") from error
            planned_results = await self._run_planned_searches(plan.searches[:5])
            searches.extend(result for result in planned_results if "error" not in result)
            messages.append(
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "plannedSearches": plan.searches,
                            "initialTavilyResults": planned_results,
                        },
                        ensure_ascii=False,
                        default=str,
                    ),
                }
            )

        for _ in range(self._max_rounds):
            response = await self._request(messages)
            message = response.choices[0].message
            tool_calls = cast(list[Any], getattr(message, "tool_calls", None) or [])

            if not tool_calls:
                return await self._finalize_layer1(
                    getattr(message, "content", None), searches
                )

            messages.append(_assistant_tool_message(message, tool_calls))
            await self._append_tool_results(messages, tool_calls, searches)

        raise ResearchAgentError("The research agent exceeded its search-round limit.")

    async def _finalize_layer1(
        self,
        content: Any,
        searches: list[dict[str, Any]],
    ) -> Layer1Input:
        if self._extractor:
            try:
                extraction = await self._extractor.extract(
                    [{"assistantSummary": content, "searchResults": searches}]
                )
            except FounderExtractionError as error:
                raise ResearchAgentError("The founder extraction step failed.") from error
            payload = Layer1Input.model_validate(
                {
                    "tavily": {
                        "founders": [
                            founder.model_dump(mode="json")
                            for founder in extraction.founders
                        ]
                    }
                }
            )
            payload.tavily["searches"] = searches
            return self._attach_metadata(payload)
        return self._build_layer1_profile(content, searches)

    async def _run_planned_searches(self, queries: list[str]) -> list[dict[str, Any]]:
        return [await self._run_search_query(query) for query in queries]

    async def _run_search_query(self, query: str) -> dict[str, Any]:
        try:
            result = await asyncio.to_thread(self._tavily.search, query, max_results=5)
        except Exception as error:  # Return a recoverable result to the model.
            return {"query": query, "error": f"Tavily search failed: {error}"}
        return {
            "query": query,
            "answer": result.get("answer"),
            "sources": result.get("results", []),
        }

    async def _request(self, messages: list[dict[str, Any]]) -> Any:
        try:
            return await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=[TAVILY_TOOL],
                tool_choice="auto",
                response_format={"type": "json_object"},
            )
        except Exception as error:  # Do not expose provider details or credentials.
            raise ResearchAgentError("The research model request failed.") from error

    async def _append_tool_results(
        self,
        messages: list[dict[str, Any]],
        tool_calls: list[Any],
        searches: list[dict[str, Any]],
    ) -> None:
        for tool_call in tool_calls:
            result = await self._dispatch_tool_call(tool_call)
            if "error" not in result:
                searches.append(result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": _tool_call_id(tool_call),
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

    async def _dispatch_tool_call(self, tool_call: Any) -> dict[str, Any]:
        tool_name = _tool_call_name(tool_call)
        if tool_name != "tavily_search":
            return {"error": f"Unsupported tool: {tool_name}"}
        return await self._run_tavily_tool(tool_call)

    async def _run_tavily_tool(self, tool_call: Any) -> dict[str, Any]:
        try:
            arguments = json.loads(_tool_call_arguments(tool_call))
            search_query = str(arguments["query"]).strip()
            max_results = min(max(int(arguments.get("max_results", 5)), 1), 10)
            if not search_query:
                raise ValueError("query must not be empty")
        except (KeyError, TypeError, ValueError) as error:
            return {"error": f"Invalid tavily_search arguments: {error}"}

        try:
            result = await asyncio.to_thread(
                self._tavily.search,
                search_query,
                max_results=max_results,
            )
        except Exception as error:  # Provider errors are returned to the agent for recovery.
            return {"error": f"Tavily search failed: {error}"}

        return {
            "query": search_query,
            "answer": result.get("answer"),
            "sources": result.get("results", []),
        }

    @staticmethod
    def _attach_metadata(payload: Layer1Input) -> Layer1Input:
        metadata = payload.metadata
        metadata.collectedAt = metadata.collectedAt or datetime.now(UTC).isoformat()
        metadata.dataSources = list(dict.fromkeys([*metadata.dataSources, "tavily"]))
        payload.metadata = metadata
        return payload

    @staticmethod
    def _build_layer1_profile(
        content: Any,
        searches: list[dict[str, Any]],
    ) -> Layer1Input:
        if not isinstance(content, str) or not content.strip():
            raise ResearchAgentError("The research agent returned an empty response.")
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise TypeError("response must be a JSON object")
            payload = Layer1Input.model_validate(parsed)
        except (json.JSONDecodeError, TypeError, ValidationError) as error:
            raise ResearchAgentError(
                "The research agent response did not match Layer1Input."
            ) from error

        tavily_payload = dict(payload.tavily)
        existing_searches = tavily_payload.get("searches", [])
        if not isinstance(existing_searches, list):
            existing_searches = []
        tavily_payload["searches"] = [*existing_searches, *searches]
        payload.tavily = tavily_payload
        return VCResearchAgent._attach_metadata(payload)


def build_vc_research_agent(
    settings: Settings | None = None,
    *,
    include_extractor: bool = True,
) -> VCResearchAgent:
    """Build the configured OpenAI/Tavily research agent."""
    settings = settings or get_settings()
    if not settings.openai_api_key:
        raise IntegrationNotConfigured("VC research requires OPENAI_API_KEY.")
    tavily = build_tavily_search(settings)
    client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
    return VCResearchAgent(
        client,
        tavily,
        extractor=FounderIntelligenceExtractionAgent(client) if include_extractor else None,
        planner=SearchPlanner(client),
    )


def _assistant_tool_message(message: Any, tool_calls: list[Any]) -> dict[str, Any]:
    serialized_calls: list[dict[str, Any]] = []
    for tool_call in tool_calls:
        serialized_calls.append(
            {
                "id": _tool_call_id(tool_call),
                "type": "function",
                "function": {
                    "name": _tool_call_name(tool_call),
                    "arguments": _tool_call_arguments(tool_call),
                },
            }
        )
    return {
        "role": "assistant",
        "content": getattr(message, "content", None),
        "tool_calls": serialized_calls,
    }


def _tool_call_id(tool_call: Any) -> str:
    return str(getattr(tool_call, "id", ""))


def _tool_call_name(tool_call: Any) -> str:
    function = getattr(tool_call, "function", None)
    return str(getattr(function, "name", ""))


def _tool_call_arguments(tool_call: Any) -> str:
    function = getattr(tool_call, "function", None)
    return str(getattr(function, "arguments", "{}"))
