from datetime import datetime, timedelta, timezone

import jwt
from dotenv import dotenv_values
from pwdlib import PasswordHash

from src.app.repositories.user_repository import get_user_by_email

password_hash = PasswordHash.recommended()
ACCESS_TOKEN_EXPIRE_MINUTES = 45
config = dotenv_values(".env")


def verifica_senha_gera_jwt(email: str, senha: str):
    user = get_user_by_email(email)
    if not user:
        return None

    if not password_hash.verify(senha, user["senha_hash"]):
        return None

    expira_em = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token = jwt.encode(
        {"sub": user["id"], "exp": expira_em},
        config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    return token
