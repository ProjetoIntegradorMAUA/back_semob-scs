from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from src.app.db.session import get_database
from src.app.repositories.alert_repository import AlertRepository
from src.app.repositories.financial_repository import FinancialRepository
from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.repositories.preference_repository import PreferenceRepository
from src.app.repositories.report_repository import ReportRepository
from src.app.repositories.user_repository import UserRepository
from src.app.services.auth_service import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(database: Database = Depends(get_database)) -> UserRepository:
    return UserRepository(database)


def get_operation_repository(database: Database = Depends(get_database)) -> OperationRepository:
    return OperationRepository(database)


def get_passenger_repository(database: Database = Depends(get_database)) -> PassengerRepository:
    return PassengerRepository(database)


def get_financial_repository(database: Database = Depends(get_database)) -> FinancialRepository:
    return FinancialRepository(database)


def get_hourly_operation_repository(
    database: Database = Depends(get_database),
) -> HourlyOperationRepository:
    return HourlyOperationRepository(database)


def get_alert_repository(database: Database = Depends(get_database)) -> AlertRepository:
    return AlertRepository(database)


def get_preference_repository(database: Database = Depends(get_database)) -> PreferenceRepository:
    return PreferenceRepository(database)


def get_report_repository(database: Database = Depends(get_database)) -> ReportRepository:
    return ReportRepository(database)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> dict:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise error
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise error
    user = repository.get(user_id)
    if user is None or not user.get("ativo", True):
        raise error
    return user
