from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.api.dependencies import (
    get_financial_repository,
    get_hourly_operation_repository,
    get_operation_repository,
    get_passenger_repository,
)
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.schemas.analytics import (
    FinancialAnalytics,
    OperationAnalytics,
    PassengerAnalytics,
)
from src.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Análises"])


def _service(
    operations: Annotated[OperationRepository, Depends(get_operation_repository)],
    passengers: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    financials: Annotated[FinancialRepository, Depends(get_financial_repository)],
    hourly: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
) -> AnalyticsService:
    return AnalyticsService(operations, passengers, financials, hourly)


def _validate_period(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="Período inválido.")


@router.get("/operations", response_model=OperationAnalytics)
def operation_analytics(
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    service: Annotated[AnalyticsService, Depends(_service)],
):
    _validate_period(start_date, end_date)
    return service.operation(start_date, end_date)


@router.get("/passengers", response_model=PassengerAnalytics)
def passenger_analytics(
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    service: Annotated[AnalyticsService, Depends(_service)],
):
    _validate_period(start_date, end_date)
    return service.passenger(start_date, end_date)


@router.get("/financials", response_model=FinancialAnalytics)
def financial_analytics(
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    service: Annotated[AnalyticsService, Depends(_service)],
):
    _validate_period(start_date, end_date)
    return service.financial(start_date, end_date)
