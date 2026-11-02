from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.errors import DuplicateKeyError

from src.app.api.dependencies import get_current_user, get_user_repository
from src.app.repositories.user_repository import UserRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.user import UserCreate, UserResponse, UserUpdate
from src.app.services.auth_service import hash_password

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(
    user: UserCreate,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
):
    data = user.model_dump(exclude={"senha"})
    data["email"] = str(user.email).lower()
    data["senha_hash"] = hash_password(user.senha)
    data["ativo"] = True
    try:
        return repository.create(data)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.") from error


@router.get("")
def list_users(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    _: Annotated[dict, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    name: str | None = None,
):
    items, total = repository.list(page, page_size, name)
    return {"items": items, "meta": PaginationMeta(page=page, page_size=page_size, total=total)}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    user = repository.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    data: UserUpdate,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in changes:
        changes["email"] = str(changes["email"]).lower()
    try:
        user = repository.update(user_id, changes)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.") from error
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    user = repository.delete(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
