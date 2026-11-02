from src.app.repositories.time_series_repository import TimeSeriesRepository


class PassengerRepository(TimeSeriesRepository):
    collection_name = "passengers"
