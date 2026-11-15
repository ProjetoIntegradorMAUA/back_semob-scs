from datetime import datetime
from typing import Any, Mapping

from pydantic import EmailStr, Field, model_validator

from src.app.schemas.common import ApiSchema
from src.app.schemas.common import PaginationMeta


class UserCreate(ApiSchema):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class UserUpdate(ApiSchema):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    ativo: bool | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class UserResponse(ApiSchema):
    id: str
    nome: str
    email: EmailStr
    ativo: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_document(cls, user: Mapping[str, Any]):
        return cls(
            id=str(user["id"]),
            nome=user["nome"],
            email=user["email"],
            ativo=user.get("ativo", True),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
        )


class UserList(ApiSchema):
    items: list[UserResponse]
    meta: PaginationMeta


class UserLogin(ApiSchema):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class CurrentUserUpdate(ApiSchema):
    nome: str = Field(min_length=2, max_length=120)


class PasswordChange(ApiSchema):
    senha_atual: str = Field(min_length=1, max_length=128)
    nova_senha: str = Field(min_length=8, max_length=128)
    confirmacao_senha: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.nova_senha == self.senha_atual:
            raise ValueError("A nova senha deve ser diferente da senha atual.")
        if self.nova_senha != self.confirmacao_senha:
            raise ValueError("A confirmação não confere com a nova senha.")
        return self


class TokenResponse(ApiSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
