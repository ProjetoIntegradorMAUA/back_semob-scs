from unittest.mock import MagicMock

from src.app.db.indexes import ensure_indexes


def test_ensure_indexes_includes_import_history_and_natural_keys():
    database = MagicMock()

    ensure_indexes(database)

    database.users.create_index.assert_any_call("email", unique=True)
    database.operations.create_index.assert_called_once()
    database.hourly_operations.create_index.assert_called_once()
    database.passengers.create_index.assert_called_once_with("date", unique=True)
    database.financials.create_index.assert_called_once_with("date", unique=True)
    assert database.alerts.create_index.call_count == 3
    database.preferences.create_index.assert_called_once_with("user_id", unique=True)
    database.report_jobs.create_index.assert_called_once()
    assert database.import_jobs.create_index.call_count == 2
