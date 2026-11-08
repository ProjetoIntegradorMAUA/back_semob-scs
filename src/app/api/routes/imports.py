from hashlib import sha256
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from src.app.api.dependencies import (
    get_current_user,
    get_financial_repository,
    get_hourly_operation_repository,
    get_import_job_repository,
    get_operation_repository,
    get_passenger_repository,
)
from src.app.models.common import DataSource, ImportStatus
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.repositories.import_job_repository import ImportJobRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.import_data import (
    ImportJobList,
    ImportJobResponse,
    ImportResponse,
    ImportType,
    SmartDataBatch,
    SmartDataBatchResponse,
)
from src.app.services.smart_report_parser import PARSERS

router = APIRouter(prefix="/imports", tags=["Importação"])


def _start_job(
    repository: ImportJobRepository,
    user_id: str,
    source: DataSource,
    import_type: str,
    *,
    file_name: str | None = None,
    checksum: str | None = None,
    dry_run: bool = False,
):
    return repository.create(
        {
            "requested_by": user_id,
            "source": source.value,
            "import_type": import_type,
            "file_name": file_name,
            "checksum_sha256": checksum,
            "dry_run": dry_run,
            "status": ImportStatus.PROCESSING.value,
            "parsed": 0,
            "inserted_or_updated": 0,
            "counts": {},
            "error_message": None,
        }
    )


def _fail_job(repository: ImportJobRepository, import_id: str, message: str) -> None:
    repository.update(
        import_id,
        {"status": ImportStatus.FAILED.value, "error_message": message},
    )


@router.get("/history", response_model=ImportJobList)
def list_import_history(
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ImportJobRepository, Depends(get_import_job_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items, total = repository.list_for_user(user["id"], page, page_size)
    return ImportJobList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/history/{import_id}", response_model=ImportJobResponse)
def get_import_history(
    import_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ImportJobRepository, Depends(get_import_job_repository)],
):
    item = repository.get_for_user(import_id, user["id"])
    if item is None:
        raise HTTPException(status_code=404, detail="Importação não encontrada.")
    return item


@router.post("/smart-data", response_model=SmartDataBatchResponse)
def import_smart_data(
    data: SmartDataBatch,
    user: Annotated[dict, Depends(get_current_user)],
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    hourly_operations: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    jobs: Annotated[ImportJobRepository, Depends(get_import_job_repository)],
    dry_run: bool = False,
):
    def rows(items):
        return [
            {
                **item.model_dump(mode="python"),
                "source": DataSource.SMART_DATA_API.value,
            }
            for item in items
        ]

    prepared = {
        "operations": rows(data.operations),
        "passengers": rows(data.passengers),
        "financials": rows(data.financials),
        "hourly_operations": rows(data.hourly_operations),
    }
    job = _start_job(
        jobs,
        user["id"],
        DataSource.SMART_DATA_API,
        "smart_data_batch",
        dry_run=dry_run,
    )
    if dry_run:
        counts = {name: len(items) for name, items in prepared.items()}
        result_status = ImportStatus.VALIDATED
    else:
        try:
            counts = {
                "operations": operations.upsert_many(prepared["operations"]),
                "passengers": passengers.upsert_many(prepared["passengers"]),
                "financials": financials.upsert_many(prepared["financials"]),
                "hourly_operations": hourly_operations.upsert_many(
                    prepared["hourly_operations"]
                ),
            }
        except Exception as error:
            _fail_job(jobs, job["id"], "Falha ao persistir o lote Smart Data.")
            raise HTTPException(
                status_code=500, detail="Falha ao importar lote."
            ) from error
        result_status = ImportStatus.COMPLETED

    parsed = sum(len(items) for items in prepared.values())
    changed = 0 if dry_run else sum(counts.values())
    jobs.update(
        job["id"],
        {
            "status": result_status.value,
            "parsed": parsed,
            "inserted_or_updated": changed,
            "counts": counts,
        },
    )
    return {
        "import_id": job["id"],
        **counts,
        "total": sum(counts.values()),
        "dry_run": dry_run,
        "status": result_status,
    }


@router.post("/smart-report", response_model=ImportResponse)
async def import_smart_report(
    report_type: Annotated[ImportType, Form()],
    file: Annotated[UploadFile, File()],
    user: Annotated[dict, Depends(get_current_user)],
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    hourly_operations: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    jobs: Annotated[ImportJobRepository, Depends(get_import_job_repository)],
    dry_run: bool = False,
):
    content = await file.read()
    safe_name = Path(file.filename or "upload.html").name
    job = _start_job(
        jobs,
        user["id"],
        DataSource.SMART_REPORT,
        report_type.value,
        file_name=safe_name,
        checksum=sha256(content).hexdigest(),
        dry_run=dry_run,
    )
    if len(content) > 10 * 1024 * 1024:
        message = "Arquivo maior que 10 MB."
        _fail_job(jobs, job["id"], message)
        raise HTTPException(status_code=413, detail=message)
    if not content:
        message = "Arquivo vazio."
        _fail_job(jobs, job["id"], message)
        raise HTTPException(status_code=422, detail=message)

    try:
        parsed_rows = PARSERS[report_type.value](content)
    except ValueError as error:
        _fail_job(jobs, job["id"], str(error))
        raise HTTPException(status_code=422, detail=str(error)) from error

    repositories = {
        ImportType.OPERATIONS: operations,
        ImportType.OPERATION_LINES: operations,
        ImportType.OPERATION_FCV: operations,
        ImportType.HOURLY_OPERATIONS: hourly_operations,
        ImportType.PASSENGERS: passengers,
        ImportType.FINANCIALS: financials,
    }
    if dry_run:
        changed = 0
        result_status = ImportStatus.VALIDATED
    else:
        try:
            changed = repositories[report_type].upsert_many(parsed_rows)
        except Exception as error:
            _fail_job(jobs, job["id"], "Falha ao persistir o relatório.")
            raise HTTPException(
                status_code=500, detail="Falha ao importar relatório."
            ) from error
        result_status = ImportStatus.COMPLETED

    jobs.update(
        job["id"],
        {
            "status": result_status.value,
            "parsed": len(parsed_rows),
            "inserted_or_updated": changed,
            "counts": {report_type.value: changed},
        },
    )
    return ImportResponse(
        import_id=job["id"],
        report_type=report_type,
        parsed=len(parsed_rows),
        inserted_or_updated=changed,
        source=safe_name,
        dry_run=dry_run,
        status=result_status,
    )
