from datetime import date
from unittest.mock import MagicMock

from bson import ObjectId

from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.repositories.operation_repository import OperationRepository
from src.app.repositories.preference_repository import PreferenceRepository
from src.app.repositories.report_repository import ReportRepository


def test_operation_and_hourly_repositories_forward_optional_line_filter():
    database = MagicMock()
    operations = OperationRepository(database)
    hourly = HourlyOperationRepository(database)
    operations.paginate = MagicMock(return_value=([], 0))
    hourly.paginate = MagicMock(return_value=([], 0))

    operations.list(1, 20, date(2026, 8, 1), date(2026, 8, 31), "01")
    hourly.list(1, 20, date(2026, 8, 1), date(2026, 8, 31), "02")
    operation_query = operations.paginate.call_args.args[0]
    hourly_query = hourly.paginate.call_args.args[0]
    assert operation_query["line_code"] == "01"
    assert hourly_query["line_code"] == "02"

    operations.list(1, 20)
    hourly.list(1, 20)
    assert "line_code" not in operations.paginate.call_args.args[0]
    assert "line_code" not in hourly.paginate.call_args.args[0]


def test_preference_repository_gets_and_upserts_user_document():
    identifier = ObjectId()
    database = MagicMock()
    database.preferences.find_one.return_value = {
        "_id": identifier,
        "user_id": "u1",
    }
    database.preferences.find_one_and_update.return_value = {
        "_id": identifier,
        "user_id": "u1",
        "weekly_email_summary": True,
    }
    repository = PreferenceRepository(database)

    current = repository.get_by_user("u1")
    updated = repository.upsert("u1", {"weekly_email_summary": True})

    assert current["id"] == str(identifier)
    assert updated["weekly_email_summary"] is True
    update = database.preferences.find_one_and_update.call_args.args[1]
    assert update["$set"]["user_id"] == "u1"


def test_report_repository_lists_only_requesting_user():
    database = MagicMock()
    repository = ReportRepository(database)
    repository.paginate = MagicMock(return_value=([], 0))

    assert repository.list_for_user("u1", 2, 5) == ([], 0)
    assert repository.paginate.call_args.args == (
        {"requested_by": "u1"},
        2,
        5,
        [("created_at", -1)],
    )
