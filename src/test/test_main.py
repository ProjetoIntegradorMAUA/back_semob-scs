from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app.main import app, get_rota_teste


def test_rota_teste_legacy():
    assert get_rota_teste() == {"mensagem": "Teste Funcionando"}


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "SEMOB-SCS API"
    assert response.json()["checked_at"]
    assert response.headers["cache-control"] == "no-store"


def test_readiness_endpoint_when_database_is_available():
    with patch("src.app.api.routes.health.ping_database", return_value=True):
        with TestClient(app) as client:
            response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["database"] is True
    assert response.json()["latency_ms"] >= 0
    assert response.headers["cache-control"] == "no-store"


def test_readiness_endpoint_returns_503_when_database_is_unavailable():
    with patch("src.app.api.routes.health.ping_database", return_value=False):
        with TestClient(app) as client:
            response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] is False


def test_legacy_readiness_alias_is_kept_compatible():
    with patch("src.app.api.routes.health.ping_database", return_value=True):
        with TestClient(app) as client:
            response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
