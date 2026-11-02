from datetime import date, datetime
from unittest.mock import MagicMock

from bson import ObjectId

from src.app.repositories.base import CrudRepository, mongo_ready, serialize_document
from src.app.repositories.time_series_repository import date_filter


def test_serialize_document_does_not_mutate_original():
    identifier = ObjectId()
    original = {"_id": identifier, "name": "registro"}

    serialized = serialize_document(original)

    assert serialized == {"id": str(identifier), "name": "registro"}
    assert original["_id"] == identifier


def test_mongo_ready_converts_nested_dates():
    value = {
        "date": date(2026, 8, 1),
        "items": [{"date": date(2026, 8, 2)}],
    }

    converted = mongo_ready(value)

    assert converted["date"] == datetime(2026, 8, 1)
    assert converted["items"][0]["date"] == datetime(2026, 8, 2)


def test_date_filter_builds_inclusive_period():
    query = date_filter(date(2026, 8, 1), date(2026, 8, 31))

    assert query["date"]["$gte"] == datetime(2026, 8, 1)
    assert query["date"]["$lte"].date() == date(2026, 8, 31)


def test_crud_update_and_delete_reject_invalid_ids():
    collection = MagicMock()
    repository = CrudRepository(collection)

    assert repository.update("inválido", {"name": "novo"}) is None
    assert repository.delete("inválido") is None
    collection.find_one_and_update.assert_not_called()
    collection.find_one_and_delete.assert_not_called()
