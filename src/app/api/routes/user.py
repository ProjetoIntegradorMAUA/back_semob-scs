from fastapi import APIRouter

from src.app.repositories.user_repository import create_user
from src.app.schemas.user import UserCreate

router = APIRouter(prefix="/users")


@router.post("/create", status_code=201) # se der certo retorna um 201
def adicionar_usuario(usuario: UserCreate):
    user_id = create_user(usuario.model_dump()) # esse dump transforma o usuario (que era um model ainda) em um dicionario
    return {
        "id": user_id,
        "nome": usuario.nome,
        "email": usuario.email,
        "senha": usuario.senha,
    }
