"""Generic Tavily search adapter used by the VC research agent."""

from __future__ import annotations

from typing import Any

from tavily import TavilyClient

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings


class TavilySearch:
    """Small provider boundary for evidence-gathering searches."""

    def __init__(self, client: TavilyClient):
        self._client = client

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        search_depth: str = "advanced",
    ) -> dict[str, Any]:
        """Run a Tavily search and return its JSON-compatible response."""
        response = self._client.search(
            query=query,
            search_depth=search_depth,
            include_answer="advanced",
            max_results=max_results,
        )
        return dict(response)


def build_tavily_search(settings: Settings | None = None) -> TavilySearch:
    """Build the Tavily adapter, failing clearly when it is not configured."""
    settings = settings or get_settings()
    if not settings.tavily_api_key:
        raise IntegrationNotConfigured("VC research requires TAVILY_API_KEY.")
    return TavilySearch(TavilyClient(api_key=settings.tavily_api_key.get_secret_value()))
