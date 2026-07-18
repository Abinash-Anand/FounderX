from dataclasses import dataclass
from typing import Any

from tavily import TavilyClient

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings


@dataclass(frozen=True)
class TruthGapResult:
    query: str
    answer: str | None
    sources: list[dict[str, Any]]


class TruthGapSearch:
    """Live-search adapter used to challenge unsupported investment claims."""

    def __init__(self, client: TavilyClient):
        self._client = client

    def check(self, claim: str, *, max_results: int = 5) -> TruthGapResult:
        response = self._client.search(
            query=f"Verify or contradict this venture claim with primary evidence: {claim}",
            search_depth="advanced",
            include_answer="advanced",
            max_results=max_results,
        )
        return TruthGapResult(
            query=response["query"],
            answer=response.get("answer"),
            sources=response.get("results", []),
        )


def build_truth_gap_search(settings: Settings | None = None) -> TruthGapSearch:
    settings = settings or get_settings()
    if not settings.tavily_api_key:
        raise IntegrationNotConfigured("Truth-Gap Check requires TAVILY_API_KEY.")
    return TruthGapSearch(TavilyClient(api_key=settings.tavily_api_key.get_secret_value()))

