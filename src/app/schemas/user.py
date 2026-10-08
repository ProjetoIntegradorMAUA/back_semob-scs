from pydantic import BaseModel


class UserCreate(BaseModel):
    nome: str
    email: str
    senha: str


class UserResponse(BaseModel):
    id: str
    nome: str
    email: str
