from fastapi import APIRouter

from src.app.repositories.user_repository import create_user, get_users
from src.app.schemas.user import UserCreate, UserResponse

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

@router.get("/", response_model=list[UserResponse], status_code=200) # se der certo retorna um 200 OK
def get_all_users():
    return get_users()

