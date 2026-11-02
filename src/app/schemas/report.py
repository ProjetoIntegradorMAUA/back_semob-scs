from datetime import date, datetime
from enum import StrEnum

from pydantic import Field, model_validator

from src.app.models.common import ReportStatus
from src.app.schemas.common import ApiSchema, PaginationMeta


class ReportFormat(StrEnum):
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"


class ReportCreate(ApiSchema):
    report_type: str = Field(min_length=2, max_length=80)
    format: ReportFormat
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_period(self):
        if self.end_date < self.start_date:
            raise ValueError("A data final deve ser igual ou posterior à data inicial.")
        return self


class ReportResponse(ReportCreate):
    id: str
    requested_by: str
    status: ReportStatus
    file_url: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ReportList(ApiSchema):
    items: list[ReportResponse]
    meta: PaginationMeta
