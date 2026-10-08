from pydantic import BaseModel


class User(BaseModel):
    id: str
    nome: str
    email: str
    senha_hash: str
