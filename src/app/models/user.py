from pydantic import EmailStr

from src.app.models.common import DocumentModel


class User(DocumentModel):
    nome: str
    email: EmailStr
    senha_hash: str
    ativo: bool = True
