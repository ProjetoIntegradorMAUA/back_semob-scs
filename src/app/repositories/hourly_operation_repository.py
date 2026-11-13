from datetime import date
from typing import Any

from pymongo.database import Database

from src.app.repositories.time_series_repository import TimeSeriesRepository


class HourlyOperationRepository(TimeSeriesRepository):
    collection_name = "hourly_operations"
    unique_fields = ("date", "hour", "line_code")

    def __init__(self, database: Database):
        super().__init__(database)

    def list(
        self,
        page: int,
        page_size: int,
        start_date: date | None = None,
        end_date: date | None = None,
        line_code: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        extra = {"line_code": line_code} if line_code is not None else {}
        return super().list(page, page_size, start_date, end_date, extra)
