from fastapi import APIRouter, HTTPException

from src.app.repositories.user_repository import (
    create_user,
    delete_user_by_id,
    get_user_by_id,
    get_users,
    get_users_by_name,
    update_user_by_id,
)
from src.app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users")


@router.post("/create", status_code=201)  # se der certo retorna um 201
def adicionar_usuario(usuario: UserCreate):
    user_id = create_user(
        usuario.model_dump()
    )  # esse dump transforma o usuario (que era um model ainda) em um dicionario
    return {
        "id": user_id,
        "nome": usuario.nome,
        "email": usuario.email,
        "senha": usuario.senha,
    }


@router.get("/", response_model=list[UserResponse])
def ler_todos_usuarios():
    return get_users()


@router.get("/{user_id}", response_model=UserResponse)
def ler_usuario_por_id(user_id: str):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.get("/by-name/{user_name}", response_model=list[UserResponse])
def ler_usuario_por_nome(user_name: str):
    return get_users_by_name(user_name)


@router.patch("/{user_id}", response_model=UserResponse)
def atualizar_usuario_por_id(user_id: str, usuario: UserUpdate):
    dados = usuario.model_dump(exclude_unset=True, exclude_none=True)
    if not dados:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo para atualizar.")

    user = update_user_by_id(user_id, dados)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.delete("/{user_id}", response_model=UserResponse)
def deletar_usuario_por_id(user_id:str):
    user = delete_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user
