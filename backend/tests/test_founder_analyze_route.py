from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.intelligence.founder_extraction import FounderIntelligenceBatch
from app.intelligence.profile_models import FounderIntelligence, FounderProfile, Layer1Input
from app.main import create_app
from app.persistence import PersistenceOrchestrator


class InMemoryAnalysisGateway:
    def __init__(self) -> None:
        self.research_runs: list[dict[str, object]] = []
        self.founders: dict[str, dict[str, object]] = {}

    def create_research_run(self, payload, metadata):
        research_run_id = f"run-{len(self.research_runs) + 1}"
        document = {
            "researchRunId": research_run_id,
            "payload": payload.model_dump(mode="json"),
            "metadata": metadata,
        }
        self.research_runs.append(document)
        return SimpleNamespace(researchRunId=research_run_id, payload=payload)

    def create_founder_profile(self, profile, research_run_id=None):
        founder_id = profile.founder.id
        existing = self.founders.get(founder_id)
        version = int(existing.get("version", 0)) + 1 if existing else 1
        document = {
            "founderId": founder_id,
            "profile": profile,
            "researchRunId": research_run_id or "",
            "version": version,
        }
        if existing and existing.get("founderIntelligence"):
            document["founderIntelligence"] = existing["founderIntelligence"]
        self.founders[founder_id] = document
        return SimpleNamespace(
            founderId=founder_id,
            researchRunId=research_run_id or "",
            profile=profile,
            version=version,
            updatedAt=f"2026-07-19T12:00:0{version}+00:00",
        )

    def enrich_founder_with_founder_intelligence(self, founder_id, intelligence):
        document = self.founders[founder_id]
        document["founderIntelligence"] = intelligence.model_dump(mode="json")
        document["version"] = int(document["version"]) + 1
        return SimpleNamespace(
            founderId=founder_id,
            version=document["version"],
            updatedAt="2026-07-19T12:00:09+00:00",
        )


def test_analyze_runs_all_stages_and_preserves_persistence(monkeypatch) -> None:
    calls: list[str] = []
    gateway = InMemoryAnalysisGateway()
    persistence = PersistenceOrchestrator(gateway)

    class FakeResearchAgent:
        async def research(self, query: str) -> Layer1Input:
            calls.append("research")
            return Layer1Input(
                tavily={"searches": [{"sources": [{"url": "https://example.com"}]}]}
            )

    class FakeExtractionAgent:
        async def extract(self, search_results):
            calls.append("extract")
            return FounderIntelligenceBatch(
                founders=[
                    {
                        "founderName": "Ada Lovelace",
                        "startup": "Analytical Engine",
                        "sources": [{"url": "https://example.com"}],
                    }
                ]
            )

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    async def fake_structure(payload, client):
        calls.append("structure")
        return FounderProfile.model_validate(
            {
                "founder": {"name": "Ada Lovelace"},
                "evidence": [{"id": "source-1", "title": "Founder source"}],
            }
        )

    class FakeIntelligenceService:
        async def enrich(self, profile):
            calls.append("intelligence")
            return FounderIntelligence(strengths=["Technical depth"])

    class FakeDecisionGraph:
        async def ainvoke(self, state):
            calls.append("decision")
            return {**state, "recommendation": "advance_to_partner_review"}

    settings = SimpleNamespace(openai_api_key=SecretStr("test-key"))
    monkeypatch.setattr("app.intelligence.founder_pipeline.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.intelligence.founder_pipeline.build_persistence_orchestrator",
        lambda settings: persistence,
    )
    monkeypatch.setattr(
        "app.intelligence.founder_pipeline.build_vc_research_agent",
        lambda settings, include_extractor=True: FakeResearchAgent(),
    )
    monkeypatch.setattr(
        "app.intelligence.founder_pipeline.build_founder_extraction_agent",
        lambda settings: FakeExtractionAgent(),
    )
    monkeypatch.setattr("app.intelligence.founder_pipeline.OpenAIProfileClient", FakeClient)
    monkeypatch.setattr(
        "app.intelligence.founder_pipeline.structure_founder_profile",
        fake_structure,
    )
    monkeypatch.setattr(
        "app.intelligence.founder_pipeline.build_founder_intelligence_service",
        lambda settings: FakeIntelligenceService(),
    )
    monkeypatch.setattr(
        "app.intelligence.graph.build_decision_graph",
        lambda: FakeDecisionGraph(),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: settings,
    )

    client = TestClient(create_app())
    first = client.post(
        "/v1/founders/analyze",
        json={"query": "Michael Louis Cerebrium"},
    )
    second = client.post(
        "/v1/founders/analyze",
        json={"query": "Michael Louis Cerebrium"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    body = first.json()
    assert set(body) == {
        "metadata",
        "research",
        "founderProfile",
        "founderIntelligence",
        "investmentDecision",
    }
    assert body["founderIntelligence"]["strengths"] == ["Technical depth"]
    assert body["investmentDecision"]["recommendation"] == "advance_to_partner_review"
    assert len(gateway.research_runs) == 2
    assert len(gateway.founders) == 1
    assert gateway.founders[body["metadata"]["founderId"]]["founderIntelligence"]
    assert calls == [
        "research",
        "extract",
        "structure",
        "intelligence",
        "decision",
        "research",
        "extract",
        "structure",
        "intelligence",
        "decision",
    ]