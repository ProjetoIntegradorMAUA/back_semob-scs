from pydantic import BaseModel


class UserCreate(BaseModel):  # define os dados necessarios para criar um user
    nome: str
    email: str
    senha: str


class UserUpdate(BaseModel):  # define os campos que a pessoa quer alterar (opcionais)
    nome: str | None = None
    email: str | None = None


class UserResponse(BaseModel):  # define os campos devolvidos pela api
    id: str
    nome: str
    email: str


class UserLogin(BaseModel):
    email: str
    senha: str
