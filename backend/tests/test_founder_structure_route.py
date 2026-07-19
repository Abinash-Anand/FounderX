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

    client = TestClient(create_app())
    response = client.post(
        "/v1/founders/structure",
        json={"github": {"name": "Ada"}},
    )

    assert response.status_code == 200
    assert response.json()["founder"]["name"] == "Ada Lovelace"


def test_structure_founder_route_reports_missing_openai_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.founders.get_settings",
        lambda: SimpleNamespace(openai_api_key=None),
    )

    client = TestClient(create_app())
    response = client.post("/v1/founders/structure", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Founder structuring requires OPENAI_API_KEY."
