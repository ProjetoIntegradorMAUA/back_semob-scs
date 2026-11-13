from datetime import date, datetime
from unittest.mock import MagicMock

from bson import ObjectId

from src.app.repositories.base import (
    CrudRepository,
    mongo_ready,
    object_id,
    serialize_document,
)
from src.app.repositories.time_series_repository import date_filter


def test_serialize_document_does_not_mutate_original():
    identifier = ObjectId()
    original = {"_id": identifier, "name": "registro"}

    serialized = serialize_document(original)

    assert serialized == {"id": str(identifier), "name": "registro"}
    assert original["_id"] == identifier
    assert serialize_document(None) is None


def test_mongo_ready_converts_nested_dates():
    value = {
        "date": date(2026, 8, 1),
        "items": [{"date": date(2026, 8, 2)}],
    }

    converted = mongo_ready(value)

    assert converted["date"] == datetime(2026, 8, 1)
    assert converted["items"][0]["date"] == datetime(2026, 8, 2)
    moment = datetime(2026, 8, 3, 12, 30)
    assert mongo_ready(moment) is moment
    assert mongo_ready("unchanged") == "unchanged"


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
    assert repository.get("inválido") is None
    assert object_id("inválido") is None


def test_crud_repository_complete_lifecycle_and_pagination():
    collection = MagicMock()
    identifier = ObjectId()
    collection.insert_one.return_value.inserted_id = identifier
    collection.find_one.return_value = {"_id": identifier, "name": "registro"}
    collection.find_one_and_update.return_value = {
        "_id": identifier,
        "name": "atualizado",
    }
    collection.find_one_and_delete.return_value = {
        "_id": identifier,
        "name": "atualizado",
    }
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter(
        [{"_id": identifier, "name": "registro"}, {"name": "sem-id"}]
    )
    collection.find.return_value = cursor
    collection.count_documents.return_value = 2
    repository = CrudRepository(collection)

    created = repository.create({"name": "registro", "day": date(2026, 8, 1)})
    found = repository.get(str(identifier))
    updated = repository.update(str(identifier), {"name": "atualizado"})
    deleted = repository.delete(str(identifier))
    items, total = repository.paginate({"active": True}, 2, 10, [("name", 1)])

    assert created["id"] == str(identifier)
    assert found["name"] == "registro"
    assert updated["name"] == "atualizado"
    assert deleted["id"] == str(identifier)
    assert items[1] == {"name": "sem-id"}
    assert total == 2
    cursor.skip.assert_called_once_with(10)
