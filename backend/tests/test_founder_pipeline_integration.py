from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.intelligence.founder_extraction import FounderIntelligenceBatch
from app.intelligence.profile_models import FounderIntelligence, FounderProfile, Layer1Input
from app.main import create_app


def test_founder_pipeline_reaches_decision_evaluation(monkeypatch) -> None:
    calls: list[str] = []
    profile = FounderProfile.model_validate(
        {
            "metadata": {"profileId": "profile-123"},
            "founder": {"name": "Ada Lovelace"},
            "evidence": [{"id": "source-1", "title": "Founder website"}],
        }
    )
    layer1 = Layer1Input.model_validate(
        {"tavily": {"claims": [{"founder": "Ada Lovelace"}]}}
    )

    class FakeResearchAgent:
        async def research(self, query: str) -> Layer1Input:
            calls.append("research/query")
            return layer1

    class FakeExtractionAgent:
        async def extract(self, search_results):
            calls.append("research/extract")
            return FounderIntelligenceBatch(founders=[{"founderName": "Ada Lovelace"}])

    class FakeIntelligenceService:
        async def enrich(self, received_profile):
            assert received_profile.metadata.profileId == "profile-123"
            assert received_profile.founder.id == "profile-123"
            calls.append("founders/intelligence")
            return FounderIntelligence()

    class FakePersistence:
        def save_research_run(self, payload, metadata):
            return SimpleNamespace(researchRunId="run-123", payload=payload)

        def save_founder_profile(self, profile, research_run_id=None):
            return SimpleNamespace(version=1, updatedAt="2026-07-19T12:00:00+00:00")

        def save_founder_intelligence(self, founder_id, intelligence):
            return SimpleNamespace(version=2, updatedAt="2026-07-19T12:00:00+00:00")

    class FakeDecisionGraph:
        async def ainvoke(self, state):
            calls.append("decisions/evaluate")
            return {**state, "recommendation": "advance_to_partner_review"}

    monkeypatch.setattr(
        "app.api.routes.research.build_vc_research_agent",
        lambda: FakeResearchAgent(),
    )
    monkeypatch.setattr(
        "app.api.routes.research.build_persistence_orchestrator",
        lambda: FakePersistence(),
    )
    monkeypatch.setattr(
        "app.api.routes.research.build_founder_extraction_agent",
        lambda: FakeExtractionAgent(),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )

    async def fake_structure(payload, client):
        calls.append("founders/structure")
        return profile

    monkeypatch.setattr("app.api.routes.founders.structure_founder_profile", fake_structure)
    monkeypatch.setattr(
        "app.api.routes.founders.build_founder_intelligence_service",
        lambda settings: FakeIntelligenceService(),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_persistence_orchestrator",
        lambda settings: FakePersistence(),
    )
    monkeypatch.setattr(
        "app.intelligence.graph.build_decision_graph",
        lambda: FakeDecisionGraph(),
    )

    client = TestClient(create_app())
    assert client.post("/v1/research/query", json={"query": "Find Ada"}).status_code == 200
    assert client.post(
        "/v1/research/extract",
        json={"search_results": [{"title": "Ada"}]},
    ).status_code == 200
    assert client.post(
        "/v1/founders/structure",
        json={"github": {"name": "Ada"}},
    ).status_code == 200
    assert client.post(
        "/v1/founders/intelligence",
        json=profile.model_dump(mode="json"),
    ).status_code == 200
    assert client.post(
        "/v1/decisions/evaluate",
        json={"company_name": "Analytical Engine"},
    ).status_code == 200

    assert calls == [
        "research/query",
        "research/extract",
        "founders/structure",
        "founders/intelligence",
        "decisions/evaluate",
    ]