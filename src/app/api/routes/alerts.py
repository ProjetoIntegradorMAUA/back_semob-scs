from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from src.app.api.dependencies import (
    get_alert_repository,
    get_current_user,
    get_financial_repository,
    get_operation_repository,
)
from src.app.core.config import get_settings
from src.app.models.common import AlertSeverity, AlertStatus
from src.app.repositories.alert_repository import AlertRepository
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.schemas.alert import (
    AlertCreate,
    AlertGenerationResponse,
    AlertList,
    AlertResponse,
    AlertUpdate,
)
from src.app.schemas.common import PaginationMeta
from src.app.services.anomaly_detection_service import AnomalyDetectionService

router = APIRouter(prefix="/alerts", tags=["Alertas"])


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    data: AlertCreate,
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    return repository.create(data.model_dump(mode="python"))


@router.post("/generate", response_model=AlertGenerationResponse)
def generate_alerts(
    start_date: date,
    end_date: date,
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    alerts: Annotated[AlertRepository, Depends(get_alert_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="Período inválido.")
    return AnomalyDetectionService(
        operations, financials, alerts, get_settings()
    ).generate(start_date, end_date)


@router.get("", response_model=AlertList)
def list_alerts(
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
    start_date: date | None = None,
    end_date: date | None = None,
    alert_status: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
):
    items, total = repository.list(
        page, page_size, start_date, end_date, alert_status, severity
    )
    return AlertList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: str,
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
):
    item = repository.get(alert_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return item


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: str,
    data: AlertUpdate,
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    item = repository.update(alert_id, data.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return item


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: str,
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    if repository.delete(alert_id) is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
