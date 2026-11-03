from enum import StrEnum
from datetime import date

from pydantic import Field

from src.app.schemas.financial import FinancialCreate
from src.app.schemas.operation import OperationCreate
from src.app.schemas.passenger import PassengerCreate
from src.app.schemas.common import ApiSchema


class ImportType(StrEnum):
    OPERATIONS = "operations"
    OPERATION_LINES = "operation_lines"
    OPERATION_FCV = "operation_fcv"
    HOURLY_OPERATIONS = "hourly_operations"
    PASSENGERS = "passengers"
    FINANCIALS = "financials"


class ImportResponse(ApiSchema):
    report_type: ImportType
    parsed: int
    inserted_or_updated: int
    source: str


class HourlyOperationImport(ApiSchema):
    date: date
    hour: int = Field(ge=0, le=23)
    line_code: str | None = Field(default=None, max_length=30)
    vehicles: int = Field(default=0, ge=0)
    trips: int = Field(default=0, ge=0)


class SmartDataBatch(ApiSchema):
    operations: list[OperationCreate] = Field(default_factory=list, max_length=10_000)
    passengers: list[PassengerCreate] = Field(default_factory=list, max_length=10_000)
    financials: list[FinancialCreate] = Field(default_factory=list, max_length=10_000)
    hourly_operations: list[HourlyOperationImport] = Field(
        default_factory=list, max_length=20_000
    )


class SmartDataBatchResponse(ApiSchema):
    operations: int
    passengers: int
    financials: int
    hourly_operations: int
    total: int
