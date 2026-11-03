from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.app.api.dependencies import (
    get_current_user,
    get_financial_repository,
    get_hourly_operation_repository,
    get_operation_repository,
    get_passenger_repository,
)
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.schemas.import_data import (
    ImportResponse,
    ImportType,
    SmartDataBatch,
    SmartDataBatchResponse,
)
from src.app.models.common import DataSource
from src.app.services.smart_report_parser import PARSERS

router = APIRouter(prefix="/imports", tags=["Importação"])


@router.post("/smart-data", response_model=SmartDataBatchResponse)
def import_smart_data(
    data: SmartDataBatch,
    _: Annotated[dict, Depends(get_current_user)],
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    hourly_operations: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
):
    def rows(items):
        return [
            {
                **item.model_dump(mode="python"),
                "source": DataSource.SMART_DATA_API.value,
            }
            for item in items
        ]

    counts = {
        "operations": operations.upsert_many(rows(data.operations)),
        "passengers": passengers.upsert_many(rows(data.passengers)),
        "financials": financials.upsert_many(rows(data.financials)),
        "hourly_operations": hourly_operations.upsert_many(
            rows(data.hourly_operations)
        ),
    }
    return {**counts, "total": sum(counts.values())}


@router.post("/smart-report", response_model=ImportResponse)
async def import_smart_report(
    report_type: Annotated[ImportType, Form()],
    file: Annotated[UploadFile, File()],
    _: Annotated[dict, Depends(get_current_user)],
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    hourly_operations: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
):
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo maior que 10 MB.")
    if not content:
        raise HTTPException(status_code=422, detail="Arquivo vazio.")

    try:
        rows = PARSERS[report_type.value](content)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    repositories = {
        ImportType.OPERATIONS: operations,
        ImportType.OPERATION_LINES: operations,
        ImportType.OPERATION_FCV: operations,
        ImportType.HOURLY_OPERATIONS: hourly_operations,
        ImportType.PASSENGERS: passengers,
        ImportType.FINANCIALS: financials,
    }
    changed = repositories[report_type].upsert_many(rows)
    return ImportResponse(
        report_type=report_type,
        parsed=len(rows),
        inserted_or_updated=changed,
        source=file.filename or "upload.html",
    )
