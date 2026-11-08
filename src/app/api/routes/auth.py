from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.api.dependencies import get_current_user, get_user_repository
from src.app.core.config import get_settings
from src.app.repositories.user_repository import UserRepository
from src.app.schemas.user import TokenResponse, UserLogin, UserResponse
from src.app.services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(
    user: Annotated[dict, Depends(get_current_user)],
):
    """Retorna o perfil associado ao token sem expor o hash da senha."""

    return UserResponse(
        id=user["id"],
        nome=user["nome"],
        email=user["email"],
        ativo=user.get("ativo", True),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
    )


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
