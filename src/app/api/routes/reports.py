from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.app.api.dependencies import get_current_user, get_report_repository
from src.app.models.common import ReportStatus
from src.app.repositories.report_repository import ReportRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.report import ReportCreate, ReportList, ReportResponse

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
def request_report(
    data: ReportCreate,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[ReportRepository, Depends(get_report_repository)],
):
    return repository.create(
        {
            **data.model_dump(mode="python"),
            "requested_by": user["id"],
            "status": ReportStatus.PENDING.value,
            "file_url": None,
            "error_message": None,
        }
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
