from datetime import date, datetime

from pydantic import Field, model_validator

from src.app.models.common import DataSource
from src.app.schemas.common import ApiSchema, PaginationMeta


class HourlyOperationBase(ApiSchema):
    date: date
    hour: int = Field(ge=0, le=23)
    line_code: str | None = Field(default=None, min_length=1, max_length=30)
    vehicles: int = Field(default=0, ge=0)
    trips: int = Field(default=0, ge=0)
    source: DataSource = DataSource.MANUAL


class HourlyOperationCreate(HourlyOperationBase):
    pass


class HourlyOperationUpdate(ApiSchema):
    hour: int | None = Field(default=None, ge=0, le=23)
    line_code: str | None = Field(default=None, min_length=1, max_length=30)
    vehicles: int | None = Field(default=None, ge=0)
    trips: int | None = Field(default=None, ge=0)
    source: DataSource | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class HourlyOperationResponse(HourlyOperationBase):
    id: str
    created_at: datetime
    updated_at: datetime


class HourlyOperationList(ApiSchema):
    items: list[HourlyOperationResponse]
    meta: PaginationMeta
