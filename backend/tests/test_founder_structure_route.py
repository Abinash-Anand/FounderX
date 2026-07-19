from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.intelligence.profile_models import FounderProfile
from app.main import create_app


def test_structure_founder_route_returns_profile(monkeypatch) -> None:
    profile = FounderProfile.model_validate(
        {"founder": {"name": "Ada Lovelace"}, "metadata": {"profileId": "p-1"}}
    )

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    class FakePersistence:
        def save_founder_profile(self, received_profile, research_run_id=None):
            assert received_profile.founder.id == "p-1"
            assert received_profile.metadata.profileId == "p-1"
            return SimpleNamespace(version=1, updatedAt="2026-07-19T12:00:00+00:00")

    async def fake_structure_founder_profile(payload, client):
        assert payload.github["name"] == "Ada"
        assert client.api_key == "test-key"
        return profile

    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )
    monkeypatch.setattr(
        "app.api.routes.founders.OpenAIProfileClient",
        FakeClient,
    )
    monkeypatch.setattr(
        "app.api.routes.founders.structure_founder_profile",
        fake_structure_founder_profile,
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_persistence_orchestrator",
        lambda settings: FakePersistence(),
    )

    client = TestClient(create_app())
    response = client.post(
        "/v1/founders/structure",
        json={"github": {"name": "Ada"}},
    )

    assert response.status_code == 200
    assert response.json()["founder"]["name"] == "Ada Lovelace"
    assert response.json()["founder"]["id"] == "p-1"
    assert response.json()["metadata"]["profileId"] == "p-1"


def test_structure_founder_generates_identifiers_when_all_are_missing(monkeypatch) -> None:
    profile = FounderProfile.model_validate({"founder": {"name": "Ada Lovelace"}})

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    async def fake_structure_founder_profile(payload, client):
        return profile

    class FakePersistence:
        def save_founder_profile(self, received_profile, research_run_id=None):
            assert received_profile.founder.id
            assert received_profile.metadata.profileId == received_profile.founder.id
            return SimpleNamespace(version=1, updatedAt="2026-07-19T12:00:00+00:00")

    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=SecretStr("test-key")),
    )
    monkeypatch.setattr("app.api.routes.founders.OpenAIProfileClient", FakeClient)
    monkeypatch.setattr(
        "app.api.routes.founders.structure_founder_profile",
        fake_structure_founder_profile,
    )
    monkeypatch.setattr(
        "app.api.routes.founders.build_persistence_orchestrator",
        lambda settings: FakePersistence(),
    )

    response = TestClient(create_app()).post(
        "/v1/founders/structure",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["founder"]["id"]
    assert response.json()["metadata"]["profileId"] == response.json()["founder"]["id"]


def test_structure_founder_route_reports_missing_openai_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=None),
    )

    client = TestClient(create_app())
    response = client.post("/v1/founders/structure", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Founder structuring requires OPENAI_API_KEY."
