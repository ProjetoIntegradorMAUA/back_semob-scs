from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from src.app.core.config import Settings, get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_digest: str) -> bool:
    return password_hash.verify(password, password_digest)


def create_access_token(
    user_id: str,
    settings: Settings | None = None,
    session_version: int = 0,
) -> str:
    config = settings or get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=config.access_token_expire_minutes
    )
    return jwt.encode(
        {
            "sub": user_id,
            "exp": expires_at,
            "iat": datetime.now(timezone.utc),
            "sv": session_version,
        },
        config.jwt_secret_key,
        algorithm=config.jwt_algorithm,
    )


def decode_access_token_payload(
    token: str, settings: Settings | None = None
) -> dict[str, Any] | None:
    config = settings or get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            config.jwt_secret_key,
            algorithms=[config.jwt_algorithm],
        )
    except InvalidTokenError:
        return None
    subject = payload.get("sub")
    session_version = payload.get("sv", 0)
    if not isinstance(subject, str) or not isinstance(session_version, int):
        return None
    return {**payload, "sv": session_version}


def decode_access_token(token: str, settings: Settings | None = None) -> str | None:
    payload = decode_access_token_payload(token, settings)
    return str(payload["sub"]) if payload else None


def authenticate_user(repository, email: str, password: str) -> dict | None:
    user = repository.get_by_email(email)
    if not user or not user.get("ativo", True):
        return None
    if not verify_password(password, user["senha_hash"]):
        return None
    return user


def verifica_senha_gera_jwt(email: str, senha: str):
    """Compatibilidade com a rota antiga enquanto clientes migram para /api/v1."""

    from src.app.repositories.user_repository import _repository

    user = authenticate_user(_repository(), email, senha)
    return create_access_token(user["id"]) if user else None
