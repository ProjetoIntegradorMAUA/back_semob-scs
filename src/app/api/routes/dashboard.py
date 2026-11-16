from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.api.dependencies import (
    get_alert_repository,
    get_financial_repository,
    get_hourly_operation_repository,
    get_operation_repository,
    get_passenger_repository,
)
from src.app.repositories.alert_repository import AlertRepository
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.schemas.dashboard import DashboardDataCoverage, DashboardOverview
from src.app.services.dashboard_service import DataCoverageService, DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/data-coverage", response_model=DashboardDataCoverage)
def get_data_coverage(
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    hourly_operations: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
):
    return DataCoverageService(
        operations, hourly_operations, passengers, financials
    ).snapshot()


@router.get("/overview", response_model=DashboardOverview)
def get_overview(
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    alerts: Annotated[AlertRepository, Depends(get_alert_repository)],
):
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="Período inválido.")
    return DashboardService(operations, passengers, financials, alerts).overview(
        start_date, end_date
    )
