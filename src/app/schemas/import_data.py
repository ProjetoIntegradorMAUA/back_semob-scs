from enum import StrEnum

from src.app.schemas.common import ApiSchema


class ImportType(StrEnum):
    OPERATIONS = "operations"
    PASSENGERS = "passengers"
    FINANCIALS = "financials"


class ImportResponse(ApiSchema):
    report_type: ImportType
    parsed: int
    inserted_or_updated: int
    source: str
