from datetime import date, datetime

from pydantic import Field, computed_field, model_validator

from src.app.models.common import DataSource
from src.app.schemas.common import ApiSchema, PaginationMeta


class FinancialBase(ApiSchema):
    date: date
    sales: float = Field(default=0, ge=0)
    usage: float = Field(default=0, ge=0)
    credits_transferred: float = Field(default=0, ge=0)
    system_balance: float | None = None
    source: DataSource = DataSource.MANUAL


class FinancialCreate(FinancialBase):
    pass


class FinancialUpdate(ApiSchema):
    sales: float | None = Field(default=None, ge=0)
    usage: float | None = Field(default=None, ge=0)
    credits_transferred: float | None = Field(default=None, ge=0)
    system_balance: float | None = None
    source: DataSource | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class FinancialResponse(FinancialBase):
    id: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def circulating_credit(self) -> float:
        return round(self.sales - self.usage, 2)


class FinancialList(ApiSchema):
    items: list[FinancialResponse]
    meta: PaginationMeta
