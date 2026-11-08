from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.app.api.dependencies import get_current_user
from src.app.main import app


def test_authenticated_user_profile_hides_sensitive_fields():
    now = datetime.now(timezone.utc)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "66f000000000000000000001",
        "nome": "Gestor SEMOB",
        "email": "gestor@semob.com.br",
        "ativo": True,
        "senha_hash": "hash-que-nao-pode-sair-na-resposta",
        "created_at": now,
        "updated_at": now,
    }
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["nome"] == "Gestor SEMOB"
    assert response.json()["email"] == "gestor@semob.com.br"
    assert "senha_hash" not in response.json()


def test_authenticated_user_profile_requires_bearer_token():
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
