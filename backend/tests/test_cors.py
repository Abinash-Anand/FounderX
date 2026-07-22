from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import create_app

VERCEL_ORIGIN = "https://founder-mju672edf-abinash-anands-projects.vercel.app"


def test_vercel_origin_is_allowed_for_founder_analysis(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", f'["{VERCEL_ORIGIN}"]')
    get_settings.cache_clear()
    try:
        response = TestClient(create_app()).options(
            "/v1/founders/analyze",
            headers={
                "Origin": VERCEL_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == VERCEL_ORIGIN
