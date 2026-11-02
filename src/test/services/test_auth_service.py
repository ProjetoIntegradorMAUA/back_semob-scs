from datetime import timedelta

import jwt

from src.app.core.config import Settings
from src.app.services.auth_service import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class UserRepository:
    def __init__(self, user):
        self.user = user

    def get_by_email(self, email):
        return self.user


def test_password_hash_and_authentication_flow():
    digest = hash_password("senha-segura")
    repository = UserRepository(
        {
            "id": "66f000000000000000000001",
            "email": "gestor@semob.test",
            "senha_hash": digest,
            "ativo": True,
        }
    )

    assert verify_password("senha-segura", digest)
    assert not verify_password("senha-errada", digest)
    assert authenticate_user(repository, "gestor@semob.test", "senha-segura")
    assert authenticate_user(repository, "gestor@semob.test", "senha-errada") is None


def test_inactive_user_cannot_authenticate():
    repository = UserRepository({"ativo": False, "senha_hash": "não-usado"})

    assert authenticate_user(repository, "inativo@semob.test", "senha") is None


def test_access_token_round_trip_and_invalid_token():
    settings = Settings(
        jwt_secret_key="uma-chave-de-teste-com-mais-de-trinta-e-dois-bytes",
        access_token_expire_minutes=10,
    )
    token = create_access_token("user-123", settings)

    assert decode_access_token(token, settings) == "user-123"
    assert decode_access_token(f"{token}corrompido", settings) is None


def test_expired_token_is_rejected():
    settings = Settings(
        jwt_secret_key="uma-chave-de-teste-com-mais-de-trinta-e-dois-bytes"
    )
    token = jwt.encode(
        {"sub": "user-123", "exp": 0},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    assert decode_access_token(token, settings) is None
