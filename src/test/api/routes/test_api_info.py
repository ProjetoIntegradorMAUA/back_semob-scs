from fastapi.testclient import TestClient

from src.app.main import app


def test_api_root_exposes_discovery_links():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "service": "SEMOB-SCS API",
        "version": "1.0.0",
        "api_prefix": "/api/v1",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "health": {
            "liveness": "/health",
            "readiness": "/health/ready",
        },
    }


def test_openapi_documents_root_and_hides_legacy_test_route():
    schema = app.openapi()

    assert "/" in schema["paths"]
    assert schema["paths"]["/"]["get"]["tags"] == ["Informações"]
    assert "/teste" not in schema["paths"]
