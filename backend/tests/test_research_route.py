from fastapi.testclient import TestClient

from app.intelligence.founder_extraction import (
    FounderIntelligence,
    FounderIntelligenceBatch,
)
from app.intelligence.profile_models import Layer1Input
from app.intelligence.search_planner import SearchPlan
from app.main import create_app
from app.persistence import PersistenceOrchestrator


def test_search_plan_route_returns_focused_queries(monkeypatch) -> None:
    class FakePlanner:
        async def plan(self, query: str) -> SearchPlan:
            assert query == "Find AI infrastructure founders"
            return SearchPlan(
                searches=[
                    "AI infrastructure startups",
                    "AI infrastructure startup founders",
                ]
            )

    monkeypatch.setattr(
        "app.api.routes.research.build_search_planner",
        lambda: FakePlanner(),
    )

    response = TestClient(create_app()).post(
        "/v1/research/plan",
        json={"query": "Find AI infrastructure founders"},
    )

    assert response.status_code == 200
    assert response.json()["searches"] == [
        "AI infrastructure startups",
        "AI infrastructure startup founders",
    ]


def test_founder_extraction_route_returns_structured_data(monkeypatch) -> None:
    class FakeExtractor:
        async def extract(self, search_results):
            assert search_results[0]["url"] == "https://example.com/ada"
            return FounderIntelligenceBatch(
                founders=[FounderIntelligence(founderName="Ada Lovelace")]
            )

    monkeypatch.setattr(
        "app.api.routes.research.build_founder_extraction_agent",
        lambda: FakeExtractor(),
    )

    response = TestClient(create_app()).post(
        "/v1/research/extract",
        json={"search_results": [{"url": "https://example.com/ada"}]},
    )

    assert response.status_code == 200
    assert response.json()["founders"][0]["founderName"] == "Ada Lovelace"
    assert response.json()["founders"][0]["startup"] is None


def test_research_route_returns_layer1_payload(monkeypatch) -> None:
    payload = Layer1Input.model_validate(
        {"tavily": {"claims": [{"founder": "Ada Lovelace"}]}}
    )

    class FakeAgent:
        async def research(self, query: str) -> Layer1Input:
            assert query == "Find AI infrastructure founders"
            return payload

    monkeypatch.setattr(
        "app.api.routes.research.build_vc_research_agent",
        lambda: FakeAgent(),
    )

    response = TestClient(create_app()).post(
        "/v1/research/query",
        json={"query": "Find AI infrastructure founders"},
    )

    assert response.status_code == 200
    assert response.json()["tavily"]["claims"][0]["founder"] == "Ada Lovelace"


def test_research_route_persists_research_run_and_returns_id(monkeypatch) -> None:
    payload = Layer1Input.model_validate(
        {"tavily": {"claims": [{"founder": "Ada Lovelace"}]}}
    )

    class FakeAgent:
        async def research(self, query: str) -> Layer1Input:
            assert query == "Find AI infrastructure founders"
            return payload

    class FakeGateway:
        def __init__(self) -> None:
            self.saved_documents: list[dict[str, object]] = []

        def create_research_run(self, research_run, metadata):
            document = research_run.model_dump(mode="json")
            document.update(
                {
                    "researchRunId": "run-123",
                    "rawResponses": [],
                    "immutable": True,
                    "metadata": metadata,
                }
            )
            self.saved_documents.append(document)
            return type(
                "StoredResearchRun",
                (),
                {
                    "researchRunId": "run-123",
                    "payload": document,
                    "rawResponses": [],
                    "immutable": True,
                },
            )()

    fake_gateway = FakeGateway()
    monkeypatch.setattr(
        "app.api.routes.research.build_vc_research_agent",
        lambda: FakeAgent(),
    )
    monkeypatch.setattr(
        "app.api.routes.research.build_persistence_orchestrator",
        lambda: PersistenceOrchestrator(fake_gateway),
    )

    response = TestClient(create_app()).post(
        "/v1/research/query",
        json={"query": "Find AI infrastructure founders"},
    )

    assert response.status_code == 200
    assert response.json()["researchRunId"] == "run-123"
    assert response.json()["tavily"]["claims"][0]["founder"] == "Ada Lovelace"
    assert fake_gateway.saved_documents[0]["immutable"] is True
    assert fake_gateway.saved_documents[0]["rawResponses"] == []


def test_research_route_returns_503_when_integrations_are_missing(monkeypatch) -> None:
    from app.core.errors import IntegrationNotConfigured

    def missing_agent() -> None:
        raise IntegrationNotConfigured("VC research requires TAVILY_API_KEY.")

    monkeypatch.setattr("app.api.routes.research.build_vc_research_agent", missing_agent)

    response = TestClient(create_app()).post(
        "/v1/research/query",
        json={"query": "Find founders"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "VC research requires TAVILY_API_KEY."
