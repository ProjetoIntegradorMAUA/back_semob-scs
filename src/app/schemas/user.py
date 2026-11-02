from datetime import datetime

from pydantic import EmailStr, Field, model_validator

from src.app.schemas.common import ApiSchema


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


class UserLogin(ApiSchema):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenResponse(ApiSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
