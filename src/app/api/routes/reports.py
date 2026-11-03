from typing import Annotated

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse

from src.app.api.dependencies import (
    get_alert_repository,
    get_current_user,
    get_financial_repository,
    get_operation_repository,
    get_passenger_repository,
    get_report_repository,
)
from src.app.core.config import get_settings
from src.app.models.common import ReportStatus
from src.app.repositories.alert_repository import AlertRepository
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.repositories.report_repository import ReportRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.report import ReportCreate, ReportList, ReportResponse
from src.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Relatórios"])


def _service(operations, passengers, financials, alerts) -> ReportService:
    return ReportService(
        operations,
        passengers,
        financials,
        alerts,
        get_settings().report_output_dir,
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def request_report(
    data: ReportCreate,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ReportRepository, Depends(get_report_repository)],
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    alerts: Annotated[AlertRepository, Depends(get_alert_repository)],
):
    report = repository.create(
        {
            **data.model_dump(mode="python"),
            "requested_by": user["id"],
            "status": ReportStatus.PENDING.value,
            "file_url": None,
            "file_name": None,
            "content_type": None,
            "error_message": None,
        }
    )
    try:
        generated = _service(operations, passengers, financials, alerts).generate(
            report["id"],
            data.report_type,
            data.format,
            data.start_date,
            data.end_date,
        )
    except Exception as error:
        repository.update(
            report["id"],
            {
                "status": ReportStatus.FAILED.value,
                "error_message": str(error),
            },
        )
        raise HTTPException(status_code=500, detail="Falha ao gerar relatório.") from error
    return repository.update(
        report["id"],
        {
            **generated,
            "status": ReportStatus.COMPLETED.value,
            "file_url": f"/api/v1/reports/{report['id']}/download",
        },
    )


@router.get("", response_model=ReportList)
def list_reports(
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ReportRepository, Depends(get_report_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items, total = repository.list_for_user(user["id"], page, page_size)
    return ReportList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ReportRepository, Depends(get_report_repository)],
):
    report = repository.get(report_id)
    if report is None or report["requested_by"] != user["id"]:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ReportRepository, Depends(get_report_repository)],
):
    report = repository.get(report_id)
    if report is None or report["requested_by"] != user["id"]:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    if report.get("status") != ReportStatus.COMPLETED.value or not report.get("file_name"):
        raise HTTPException(status_code=409, detail="Relatório ainda não está disponível.")
    path = ReportService(None, None, None, None, get_settings().report_output_dir).path(
        report["file_name"]
    )
    if not path.is_file():
        raise HTTPException(status_code=410, detail="Arquivo do relatório não está mais disponível.")
    return FileResponse(
        path,
        media_type=report.get("content_type") or "application/octet-stream",
        filename=Path(report["file_name"]).name,
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ReportRepository, Depends(get_report_repository)],
):
    report = repository.get(report_id)
    if report is None or report["requested_by"] != user["id"]:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    if report.get("file_name"):
        path = ReportService(None, None, None, None, get_settings().report_output_dir).path(
            report["file_name"]
        )
        if path.is_file():
            path.unlink()
    repository.delete(report_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
