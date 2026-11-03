from datetime import date, datetime
from unittest.mock import MagicMock

from src.app.repositories.time_series_repository import TimeSeriesRepository


class Repository(TimeSeriesRepository):
    collection_name = "series"
    unique_fields = ("date", "line_code")


def test_upsert_many_converts_natural_key_date_to_bson_datetime():
    database = MagicMock()
    collection = MagicMock()
    database.__getitem__.return_value = collection
    repository = Repository(database)

    changed = repository.upsert_many(
        [{"date": date(2026, 8, 1), "line_code": "01", "value": 10}]
    )

    assert changed == 1
    request = collection.bulk_write.call_args.args[0][0]
    assert request._filter["date"] == datetime(2026, 8, 1)
    assert request._filter["line_code"] == "01"


def test_upsert_many_skips_database_when_batch_is_empty():
    database = MagicMock()
    collection = MagicMock()
    database.__getitem__.return_value = collection
    repository = Repository(database)

    assert repository.upsert_many([]) == 0
    collection.bulk_write.assert_not_called()
