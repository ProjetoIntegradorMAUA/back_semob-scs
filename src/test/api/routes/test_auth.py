from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.app.api.dependencies import get_current_user, get_user_repository
from src.app.api.routes import auth
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


class Users:
    def __init__(self, user):
        self.user = user
        self.fail = False

    def update(self, user_id, changes):
        if self.fail:
            return None
        self.user.update(changes)
        return self.user


def test_authenticated_user_can_update_own_name_and_password(monkeypatch):
    user = {
        "id": "66f000000000000000000001",
        "nome": "Gestor SEMOB",
        "email": "gestor@semob.com.br",
        "ativo": True,
        "senha_hash": "hash-antigo",
    }
    repository = Users(user)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_user_repository] = lambda: repository
    monkeypatch.setattr(auth, "verify_password", lambda password, digest: password == "atual123")
    monkeypatch.setattr(auth, "hash_password", lambda password: f"hash:{password}")
    try:
        with TestClient(app) as client:
            profile = client.patch(
                "/api/v1/auth/me",
                json={"nome": "Novo Gestor"},
            )
            password = client.put(
                "/api/v1/auth/me/password",
                json={
                    "senha_atual": "atual123",
                    "nova_senha": "nova-senha-123",
                    "confirmacao_senha": "nova-senha-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert profile.status_code == 200
    assert profile.json()["nome"] == "Novo Gestor"
    assert password.status_code == 204
    assert user["senha_hash"] == "hash:nova-senha-123"


def test_profile_changes_validate_credentials_and_missing_user(monkeypatch):
    user = {
        "id": "66f000000000000000000001",
        "nome": "Gestor SEMOB",
        "email": "gestor@semob.com.br",
        "ativo": True,
        "senha_hash": "hash-antigo",
    }
    repository = Users(user)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_user_repository] = lambda: repository
    monkeypatch.setattr(auth, "verify_password", lambda *args: False)
    try:
        with TestClient(app) as client:
            wrong_password = client.put(
                "/api/v1/auth/me/password",
                json={
                    "senha_atual": "errada",
                    "nova_senha": "nova-senha-123",
                    "confirmacao_senha": "nova-senha-123",
                },
            )
            mismatch = client.put(
                "/api/v1/auth/me/password",
                json={
                    "senha_atual": "atual123",
                    "nova_senha": "nova-senha-123",
                    "confirmacao_senha": "outra-senha-123",
                },
            )
            same_password = client.put(
                "/api/v1/auth/me/password",
                json={
                    "senha_atual": "mesma-senha",
                    "nova_senha": "mesma-senha",
                    "confirmacao_senha": "mesma-senha",
                },
            )

            repository.fail = True
            missing_profile = client.patch(
                "/api/v1/auth/me",
                json={"nome": "Novo Gestor"},
            )
            monkeypatch.setattr(auth, "verify_password", lambda *args: True)
            missing_password = client.put(
                "/api/v1/auth/me/password",
                json={
                    "senha_atual": "atual123",
                    "nova_senha": "nova-senha-123",
                    "confirmacao_senha": "nova-senha-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert wrong_password.status_code == 400
    assert mismatch.status_code == 422
    assert same_password.status_code == 422
    assert missing_profile.status_code == 404
    assert missing_password.status_code == 404
