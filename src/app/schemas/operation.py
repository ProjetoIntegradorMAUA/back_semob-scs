from datetime import date, datetime

from pydantic import Field, computed_field, model_validator

from src.app.models.common import DataSource
from src.app.schemas.common import ApiSchema, PaginationMeta


class OperationBase(ApiSchema):
    date: date
    line_code: str | None = Field(default=None, min_length=1, max_length=30)
    vehicles_operated: int = Field(default=0, ge=0)
    max_vehicles_in_service: int = Field(default=0, ge=0)
    scheduled_trips: int = Field(default=0, ge=0)
    completed_trips: int = Field(default=0, ge=0)
    productive_km: float = Field(default=0, ge=0)
    deadhead_km: float = Field(default=0, ge=0)
    source: DataSource = DataSource.MANUAL


class OperationCreate(OperationBase):
    pass


class OperationUpdate(ApiSchema):
    line_code: str | None = Field(default=None, min_length=1, max_length=30)
    vehicles_operated: int | None = Field(default=None, ge=0)
    max_vehicles_in_service: int | None = Field(default=None, ge=0)
    scheduled_trips: int | None = Field(default=None, ge=0)
    completed_trips: int | None = Field(default=None, ge=0)
    productive_km: float | None = Field(default=None, ge=0)
    deadhead_km: float | None = Field(default=None, ge=0)
    source: DataSource | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class OperationResponse(OperationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def missing_trips(self) -> int:
        return max(self.scheduled_trips - self.completed_trips, 0)

    @computed_field
    @property
    def total_km(self) -> float:
        return round(self.productive_km + self.deadhead_km, 2)

    @computed_field
    @property
    def completion_rate(self) -> float:
        if self.scheduled_trips == 0:
            return 0
        return round(self.completed_trips / self.scheduled_trips * 100, 2)


class OperationList(ApiSchema):
    items: list[OperationResponse]
    meta: PaginationMeta
