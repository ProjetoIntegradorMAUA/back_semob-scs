from datetime import date, datetime
from unittest.mock import MagicMock

from bson import ObjectId

from src.app.models.common import AlertRule, AlertSeverity, AlertStatus
from src.app.repositories.alert_repository import AlertRepository


def test_upsert_generated_uses_natural_key_and_preserves_status():
    database = MagicMock()
    database.alerts.update_one.return_value.upserted_id = ObjectId()
    repository = AlertRepository(database)

    created = repository.upsert_generated(
        {
            "date": date(2026, 8, 1),
            "line_code": "01",
            "rule_code": AlertRule.TRIP_COMPLETION_LOW.value,
            "type": "Baixo cumprimento",
            "description": "Cumprimento abaixo do limite.",
            "severity": "attention",
        }
    )

    query, update = database.alerts.update_one.call_args.args
    assert created is True
    assert query["rule_code"] == AlertRule.TRIP_COMPLETION_LOW.value
    assert query["line_code"] == "01"
    assert update["$setOnInsert"]["status"] == AlertStatus.OPEN.value
    assert "status" not in update["$set"]


def test_resolve_stale_generated_keeps_active_alerts():
    active_id = ObjectId()
    stale_id = ObjectId()
    database = MagicMock()
    database.alerts.find.return_value = [
        {
            "_id": active_id,
            "rule_code": AlertRule.TRIP_COMPLETION_LOW.value,
            "date": datetime(2026, 8, 1),
            "line_code": "01",
        },
        {
            "_id": stale_id,
            "rule_code": AlertRule.NEGATIVE_CIRCULATING_CREDIT.value,
            "date": datetime(2026, 8, 2),
            "line_code": None,
        },
    ]
    database.alerts.update_many.return_value.modified_count = 1
    repository = AlertRepository(database)

    resolved = repository.resolve_stale_generated(
        date(2026, 8, 1),
        date(2026, 8, 31),
        {(AlertRule.TRIP_COMPLETION_LOW.value, "2026-08-01", "01")},
    )

    assert resolved == 1
    update_query = database.alerts.update_many.call_args.args[0]
    assert update_query == {"_id": {"$in": [stale_id]}}


def test_alert_queries_apply_filters_count_and_serialize_ranges():
    identifier = ObjectId()
    database = MagicMock()
    repository = AlertRepository(database)
    repository.paginate = MagicMock(return_value=([], 0))

    repository.list(
        1,
        10,
        date(2026, 8, 1),
        date(2026, 8, 31),
        AlertStatus.OPEN,
        AlertSeverity.CRITICAL,
    )
    query = repository.paginate.call_args.args[0]
    assert query["status"] == "open"
    assert query["severity"] == "critical"

    database.alerts.count_documents.return_value = 4
    assert repository.count_open(date(2026, 8, 1), date(2026, 8, 31)) == 4
    count_query = database.alerts.count_documents.call_args.args[0]
    assert count_query["status"] == {"$ne": "resolved"}

    cursor = MagicMock()
    cursor.sort.return_value = [{"_id": identifier, "type": "Teste"}]
    database.alerts.find.return_value = cursor
    assert repository.find_range(date(2026, 8, 1), date(2026, 8, 31))[0][
        "id"
    ] == str(identifier)


def test_resolve_stale_generated_skips_update_when_nothing_is_stale():
    database = MagicMock()
    database.alerts.find.return_value = []
    repository = AlertRepository(database)

    assert repository.resolve_stale_generated(date(2026, 8, 1), date(2026, 8, 31), set()) == 0
    database.alerts.update_many.assert_not_called()
