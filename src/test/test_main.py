import asyncio
import logging
from uuid import UUID

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from src.app.core.request_tracing import trace_request
from src.app.main import app, get_rota_teste


def test_rota_teste_legacy():
    assert get_rota_teste() == {"mensagem": "Teste Funcionando"}


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "SEMOB-SCS API"


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
