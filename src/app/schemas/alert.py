from datetime import date, datetime

from pydantic import Field, model_validator

from src.app.models.common import AlertSeverity, AlertStatus
from src.app.schemas.common import ApiSchema, PaginationMeta


class AlertCreate(ApiSchema):
    date: date
    type: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=3, max_length=500)
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN
    line_code: str | None = Field(default=None, max_length=30)
    metric: str | None = Field(default=None, max_length=80)
    observed_value: float | None = None
    expected_value: float | None = None


class AlertUpdate(ApiSchema):
    description: str | None = Field(default=None, min_length=3, max_length=500)
    severity: AlertSeverity | None = None
    status: AlertStatus | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class AlertResponse(AlertCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class AlertList(ApiSchema):
    items: list[AlertResponse]
    meta: PaginationMeta
