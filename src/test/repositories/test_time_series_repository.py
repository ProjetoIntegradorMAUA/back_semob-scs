from datetime import date, datetime
from unittest.mock import MagicMock

from src.app.repositories.time_series_repository import TimeSeriesRepository, date_filter


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


def test_list_and_find_range_apply_filters_and_serialize_documents():
    database = MagicMock()
    collection = MagicMock()
    database.__getitem__.return_value = collection
    repository = Repository(database)
    repository.paginate = MagicMock(return_value=([{"id": "1"}], 1))

    items, total = repository.list(
        1,
        20,
        date(2026, 8, 1),
        date(2026, 8, 31),
        {"line_code": "01"},
    )

    identifier = MagicMock()
    cursor = MagicMock()
    cursor.sort.return_value = [
        {"_id": identifier, "date": datetime(2026, 8, 1)},
        {"date": datetime(2026, 8, 2)},
    ]
    collection.find.return_value = cursor
    ranged = repository.find_range(
        date(2026, 8, 1), date(2026, 8, 31), {"line_code": "01"}
    )

    query = repository.paginate.call_args.args[0]
    assert items == [{"id": "1"}]
    assert total == 1
    assert query["line_code"] == "01"
    assert len(ranged) == 2
    assert date_filter(None, None) == {}
