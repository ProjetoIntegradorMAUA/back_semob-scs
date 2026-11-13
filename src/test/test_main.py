import asyncio
import logging
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from src.app.core.request_tracing import trace_request
from src.app import main
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


def test_request_tracing_generates_id_and_processing_time():
    with TestClient(app) as client:
        response = client.get("/health")

    UUID(response.headers["x-request-id"])
    assert float(response.headers["x-process-time-ms"]) >= 0


def test_request_tracing_preserves_safe_client_id_and_logs_it(caplog):
    request_id = "front-dashboard-2026.11"
    caplog.set_level(logging.INFO, logger="semob.requests")

    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": request_id})

    assert response.headers["x-request-id"] == request_id
    record = next(item for item in caplog.records if item.message == "request_completed")
    assert record.request_id == request_id
    assert record.http_method == "GET"
    assert record.http_path == "/health"
    assert record.status_code == 200


def test_request_tracing_replaces_unsafe_client_id():
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "id com espacos"})

    assert response.headers["x-request-id"] != "id com espacos"
    UUID(response.headers["x-request-id"])


def test_tracing_headers_are_exposed_to_frontend():
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

    exposed = response.headers["access-control-expose-headers"]
    assert "X-Request-ID" in exposed
    assert "X-Process-Time-Ms" in exposed


def test_request_tracing_logs_unhandled_failure(caplog):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/falha",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )

    async def fail(_: Request):
        raise RuntimeError("falha simulada")

    caplog.set_level(logging.ERROR, logger="semob.requests")
    with pytest.raises(RuntimeError, match="falha simulada"):
        asyncio.run(trace_request(request, fail))

    record = next(item for item in caplog.records if item.message == "request_failed")
    UUID(record.request_id)
    assert record.http_path == "/falha"
    assert record.duration_ms >= 0


def test_lifespan_connects_and_creates_indexes_when_enabled(monkeypatch):
    database = object()
    ensure_indexes = MagicMock()
    close_database = MagicMock()
    monkeypatch.setattr(main.settings, "mongo_connect_on_startup", True)
    monkeypatch.setattr(main, "get_database", lambda: database)
    monkeypatch.setattr(main, "ensure_indexes", ensure_indexes)
    monkeypatch.setattr(main, "close_database", close_database)

    async def run_lifespan():
        async with main.lifespan(app):
            pass

    asyncio.run(run_lifespan())

    ensure_indexes.assert_called_once_with(database)
    close_database.assert_called_once()
