from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.app.api.dependencies import get_current_user, get_user_repository
from src.app.core.config import get_settings
from src.app.repositories.user_repository import UserRepository
from src.app.schemas.user import (
    CurrentUserUpdate,
    PasswordChange,
    TokenResponse,
    UserLogin,
    UserResponse,
)
from src.app.services.auth_service import (
    authenticate_user,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _public_user(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        nome=user["nome"],
        email=user["email"],
        ativo=user.get("ativo", True),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
    )


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(
    user: Annotated[dict, Depends(get_current_user)],
):
    """Retorna o perfil associado ao token sem expor o hash da senha."""

    return _public_user(user)


@router.patch("/me", response_model=UserResponse)
def update_authenticated_user(
    data: CurrentUserUpdate,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[UserRepository, Depends(get_user_repository)],
):
    updated = repository.update(user["id"], {"nome": data.nome})
    if updated is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return _public_user(updated)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_authenticated_user_password(
    data: PasswordChange,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[UserRepository, Depends(get_user_repository)],
):
    if not verify_password(data.senha_atual, user["senha_hash"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    updated = repository.update(
        user["id"],
        {"senha_hash": hash_password(data.nova_senha)},
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
):
    user = authenticate_user(repository, str(data.email), data.senha)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user["id"], settings),
        expires_in=settings.access_token_expire_minutes * 60,
    )
