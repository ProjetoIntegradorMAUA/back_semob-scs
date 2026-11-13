from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.app.api import dependencies


def test_repository_dependency_factories_use_injected_database():
    database = MagicMock()
    collections = {
        name: MagicMock(name=name)
        for name in ("operations", "passengers", "financials", "hourly_operations")
    }
    database.__getitem__.side_effect = collections.__getitem__

    assert dependencies.get_user_repository(database).collection is database.users
    assert dependencies.get_operation_repository(database).collection is collections["operations"]
    assert dependencies.get_passenger_repository(database).collection is collections["passengers"]
    assert dependencies.get_financial_repository(database).collection is collections["financials"]
    assert (
        dependencies.get_hourly_operation_repository(database).collection
        is collections["hourly_operations"]
    )
    assert dependencies.get_import_job_repository(database).collection is database.import_jobs
    assert dependencies.get_alert_repository(database).collection is database.alerts
    assert dependencies.get_preference_repository(database).collection is database.preferences
    assert dependencies.get_report_repository(database).collection is database.report_jobs


def test_current_user_accepts_valid_token_and_rejects_invalid_states(monkeypatch):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    repository = MagicMock()
    repository.get.return_value = {"id": "u1", "ativo": True}
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: "u1")

    assert dependencies.get_current_user(credentials, repository)["id"] == "u1"

    for supplied_credentials, decoded, user in (
        (None, "u1", {"id": "u1", "ativo": True}),
        (credentials, None, {"id": "u1", "ativo": True}),
        (credentials, "u1", None),
        (credentials, "u1", {"id": "u1", "ativo": False}),
    ):
        monkeypatch.setattr(dependencies, "decode_access_token", lambda token, value=decoded: value)
        repository.get.return_value = user
        with pytest.raises(HTTPException) as error:
            dependencies.get_current_user(supplied_credentials, repository)
        assert error.value.status_code == 401
        assert error.value.headers == {"WWW-Authenticate": "Bearer"}
