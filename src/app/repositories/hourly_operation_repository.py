from pymongo.database import Database

from src.app.repositories.time_series_repository import TimeSeriesRepository


class HourlyOperationRepository(TimeSeriesRepository):
    collection_name = "hourly_operations"
    unique_fields = ("date", "hour", "line_code")

    def __init__(self, database: Database):
        super().__init__(database)
