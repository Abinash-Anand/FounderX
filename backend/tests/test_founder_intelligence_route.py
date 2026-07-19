from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.intelligence.founder_intelligence import FounderIntelligenceError
from app.intelligence.profile_models import FounderIntelligence, FounderProfile
from app.main import create_app


def _profile() -> dict[str, object]:
    return {
        "metadata": {"profileId": "profile-123"},
        "founder": {"name": "Ada Lovelace"},
        "evidence": [{"id": "paper-1", "title": "Published technical work"}],
    }


def _intelligence() -> FounderIntelligence:
    return FounderIntelligence(
        strengths=["Technical depth"],
        weaknesses=["Limited customer evidence"],
        executionRisks=["Hiring plan is unknown"],
        leadershipAssessment="Evidence suggests strong technical leadership.",
        technicalDepthAssessment="Published technical work supports depth.",
        marketCredibility="Market references are incomplete.",
        founderQualitySignals=["Technical founder-market fit"],
        confidenceScores=[{"dimension": "technicalDepth", "score": 0.86}],
        missingInformation=["Customer retention"],
        evidenceReferences=[
            {"insight": "Technical depth", "evidenceIds": ["paper-1"]}
        ],
        reasoning=[
            {
                "insight": "Technical depth",
                "reasoning": "The publication directly supports the claim.",
            }
        ],
    )


def test_founder_intelligence_route_enriches_and_persists_once(monkeypatch) -> None:
    intelligence = _intelligence()
    calls: list[tuple[str, object]] = []

    class FakeService:
        async def enrich(self, received_profile):
            assert received_profile.metadata.profileId == "profile-123"
            assert received_profile.founder.id == "profile-123"
            return intelligence

    class FakePersistence:
        def save_founder_intelligence(self, founder_id, received_intelligence):
            calls.append((founder_id, received_intelligence))
            return SimpleNamespace(version=2, updatedAt="2026-07-19T12:00:00+00:00")

    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_founder_intelligence_service",
        lambda settings: FakeService(),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_persistence_orchestrator",
        lambda settings: FakePersistence(),
    )

    response = TestClient(create_app()).post(
        "/v1/founders/intelligence",
        json=_profile(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["founderIntelligence"]["strengths"] == ["Technical depth"]
    assert body["profileVersion"] == 2
    assert body["metadata"]["lastUpdated"] == "2026-07-19T12:00:00+00:00"
    assert calls == [("profile-123", intelligence)]


def test_founder_intelligence_route_requires_openai(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=None),
    )

    response = TestClient(create_app()).post(
        "/v1/founders/intelligence",
        json=_profile(),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Founder intelligence requires OPENAI_API_KEY."


def test_founder_intelligence_route_maps_generation_failure_to_502(monkeypatch) -> None:
    class FakeService:
        async def enrich(self, profile):
            raise FounderIntelligenceError("bad intelligence response")

    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_founder_intelligence_service",
        lambda settings: FakeService(),
    )

    response = TestClient(create_app()).post(
        "/v1/founders/intelligence",
        json=_profile(),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "bad intelligence response"


def test_founder_intelligence_route_creates_missing_baseline_profile(monkeypatch) -> None:
    class FakeService:
        async def enrich(self, profile):
            return _intelligence()

    class FakePersistence:
        def __init__(self):
            self.created = False

        def save_founder_profile(self, profile):
            self.created = True
            return SimpleNamespace(version=1, updatedAt="2026-07-19T12:00:00+00:00")

        def save_founder_intelligence(self, founder_id, intelligence):
            if not self.created:
                raise KeyError("Founder profile 'profile-123' does not exist.")
            return SimpleNamespace(version=2, updatedAt="2026-07-19T12:00:00+00:00")

    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_founder_intelligence_service",
        lambda settings: FakeService(),
    )
    persistence = FakePersistence()
    monkeypatch.setattr(
        "app.api.routes.founders.build_persistence_orchestrator",
        lambda settings: persistence,
    )

    response = TestClient(create_app()).post(
        "/v1/founders/intelligence",
        json=_profile(),
    )

    assert response.status_code == 200
    assert response.json()["profileVersion"] == 2
    assert persistence.created is True


def test_founder_intelligence_generates_identifiers_for_direct_profile(monkeypatch) -> None:
    class FakeService:
        async def enrich(self, profile):
            assert profile.founder.id
            assert profile.metadata.profileId == profile.founder.id
            return _intelligence()

    class FakePersistence:
        def save_founder_profile(self, profile):
            return SimpleNamespace(version=1, updatedAt="2026-07-19T12:00:00+00:00")

        def save_founder_intelligence(self, founder_id, intelligence):
            return SimpleNamespace(version=2, updatedAt="2026-07-19T12:00:00+00:00")

    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_founder_intelligence_service",
        lambda settings: FakeService(),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_persistence_orchestrator",
        lambda settings: FakePersistence(),
    )

    response = TestClient(create_app()).post(
        "/v1/founders/intelligence",
        json={
            "founder": {"name": "Ada Lovelace"},
            "evidence": [{"id": "paper-1", "title": "Published technical work"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["founder"]["id"]
    assert response.json()["metadata"]["profileId"] == response.json()["founder"]["id"]


def test_founder_intelligence_profile_round_trips_as_founder_profile() -> None:
    profile = FounderProfile.model_validate(_profile())
    enriched = profile.model_copy(update={"founderIntelligence": _intelligence()})

    assert FounderProfile.model_validate(enriched.model_dump()) == enriched
