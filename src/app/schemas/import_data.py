from datetime import date, datetime
from enum import StrEnum

from pydantic import Field

from src.app.models.common import DataSource, ImportStatus
from src.app.schemas.common import ApiSchema, PaginationMeta
from src.app.schemas.financial import FinancialCreate
from src.app.schemas.operation import OperationCreate
from src.app.schemas.passenger import PassengerCreate


class ImportType(StrEnum):
    OPERATIONS = "operations"
    OPERATION_LINES = "operation_lines"
    OPERATION_FCV = "operation_fcv"
    HOURLY_OPERATIONS = "hourly_operations"
    PASSENGERS = "passengers"
    FINANCIALS = "financials"


class ImportResponse(ApiSchema):
    import_id: str
    report_type: ImportType
    parsed: int
    inserted_or_updated: int
    source: str
    dry_run: bool = False
    status: ImportStatus


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
    import_id: str
    operations: int
    passengers: int
    financials: int
    hourly_operations: int
    total: int
    dry_run: bool = False
    status: ImportStatus


class ImportJobResponse(ApiSchema):
    id: str
    requested_by: str
    source: DataSource
    import_type: str
    file_name: str | None = None
    checksum_sha256: str | None = None
    dry_run: bool
    status: ImportStatus
    parsed: int
    inserted_or_updated: int
    counts: dict[str, int]
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ImportJobList(ApiSchema):
    items: list[ImportJobResponse]
    meta: PaginationMeta
