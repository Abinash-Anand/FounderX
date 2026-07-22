import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import create_app

VERCEL_ORIGINS = [
    "https://founder-mju672edf-abinash-anands-projects.vercel.app",
    "https://founder-x-git-main-abinash-anands-projects.vercel.app",
]


@pytest.mark.parametrize("origin", VERCEL_ORIGINS)
def test_vercel_origin_is_allowed_for_founder_analysis(monkeypatch, origin: str) -> None:
    monkeypatch.setenv("CORS_ORIGINS", str(VERCEL_ORIGINS).replace("'", '"'))
    get_settings.cache_clear()
    try:
        response = TestClient(create_app()).options(
            "/v1/founders/analyze",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
