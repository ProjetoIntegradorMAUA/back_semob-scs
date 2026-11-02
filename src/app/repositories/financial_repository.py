from src.app.repositories.time_series_repository import TimeSeriesRepository


class FinancialRepository(TimeSeriesRepository):
    collection_name = "financials"
