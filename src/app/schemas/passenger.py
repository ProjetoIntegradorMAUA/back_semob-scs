from datetime import date, datetime

from pydantic import Field, computed_field, model_validator

from src.app.models.common import DataSource
from src.app.schemas.common import ApiSchema, PaginationMeta


class PassengerBase(ApiSchema):
    date: date
    fare_gate: int = Field(default=0, ge=0)
    prepaid: int = Field(default=0, ge=0)
    non_paying: int = Field(default=0, ge=0)
    source: DataSource = DataSource.MANUAL


class PassengerCreate(PassengerBase):
    pass


class PassengerUpdate(ApiSchema):
    fare_gate: int | None = Field(default=None, ge=0)
    prepaid: int | None = Field(default=None, ge=0)
    non_paying: int | None = Field(default=None, ge=0)
    source: DataSource | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class PassengerResponse(PassengerBase):
    id: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def paying(self) -> int:
        return self.fare_gate + self.prepaid

    @computed_field
    @property
    def total(self) -> int:
        return self.paying + self.non_paying


class PassengerList(ApiSchema):
    items: list[PassengerResponse]
    meta: PaginationMeta
