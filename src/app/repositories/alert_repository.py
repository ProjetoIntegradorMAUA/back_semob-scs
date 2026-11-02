from datetime import date

from pymongo import DESCENDING
from pymongo.database import Database

from src.app.models.common import AlertSeverity, AlertStatus
from src.app.repositories.base import CrudRepository
from src.app.repositories.time_series_repository import date_filter


class AlertRepository(CrudRepository):
    def __init__(self, database: Database):
        super().__init__(database.alerts)

    def list(
        self,
        page: int,
        page_size: int,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
    ):
        query = date_filter(start_date, end_date)
        if status:
            query["status"] = status.value
        if severity:
            query["severity"] = severity.value
        return self.paginate(query, page, page_size, [("date", DESCENDING)])

    def count_open(self, start_date: date, end_date: date) -> int:
        query = date_filter(start_date, end_date)
        query["status"] = {"$ne": AlertStatus.RESOLVED.value}
        return self.collection.count_documents(query)
