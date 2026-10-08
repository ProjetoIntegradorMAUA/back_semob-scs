from fastapi import APIRouter, HTTPException

from src.app.schemas.user import UserLogin
from src.app.services.auth_service import verifica_senha_gera_jwt

router = APIRouter(prefix="/api/auth")


@router.post("/login")
def logar_usuario(dados: UserLogin):
    token = verifica_senha_gera_jwt(dados.email, dados.senha)
    if token is None:
        raise HTTPException(401, detail="Email ou senha inválidos.")

    return {"access_token": token, "token_type": "bearer"}
