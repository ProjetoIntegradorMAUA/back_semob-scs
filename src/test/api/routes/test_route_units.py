from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException

from src.app.api.routes import alerts, auth, financials, operations, passengers, preferences, user
from src.app.models.common import AlertSeverity, AlertStatus
from pymongo.errors import DuplicateKeyError

from src.app.schemas.alert import AlertCreate, AlertUpdate
from src.app.schemas.financial import FinancialUpdate
from src.app.schemas.operation import OperationUpdate
from src.app.schemas.passenger import PassengerUpdate
from src.app.schemas.preference import PreferenceUpdate
from src.app.schemas.user import UserCreate, UserLogin, UserUpdate


NOW = datetime.now(timezone.utc)


class Crud:
    def __init__(self, item=None):
        self.item = item or {"id": "66f000000000000000000001"}
        self.deleted = False

    def list(self, *args):
        return [self.item], 1

    def get(self, item_id):
        return None if item_id == "missing" else self.item

    def update(self, item_id, data):
        if item_id == "missing":
            return None
        self.item.update(data)
        return self.item

    def delete(self, item_id):
        if item_id == "missing":
            return None
        self.deleted = True
        return self.item

    def create(self, data):
        self.item.update(data)
        return self.item


def _assert_not_found(callback):
    with pytest.raises(HTTPException) as error:
        callback()
    assert error.value.status_code == 404


def test_operation_passenger_and_financial_crud_routes():
    operation_repo = Crud(
        {
            "id": "1",
            "date": date(2026, 8, 1),
            "completed_trips": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert operations.list_operations(operation_repo).meta.total == 1
    assert operations.get_operation("1", operation_repo)["id"] == "1"
    assert operations.update_operation(
        "1", OperationUpdate(completed_trips=2), operation_repo, {}
    )["completed_trips"] == 2
    assert operations.delete_operation("1", operation_repo, {}).status_code == 204
    _assert_not_found(lambda: operations.get_operation("missing", operation_repo))
    _assert_not_found(
        lambda: operations.update_operation(
            "missing", OperationUpdate(completed_trips=2), operation_repo, {}
        )
    )
    _assert_not_found(lambda: operations.delete_operation("missing", operation_repo, {}))

    passenger_repo = Crud(
        {
            "id": "2",
            "date": date(2026, 8, 1),
            "fare_gate": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert passengers.create_passenger(
        passengers.PassengerCreate(date=date(2026, 8, 1)), passenger_repo, {}
    )["id"] == "2"
    assert passengers.list_passengers(passenger_repo).meta.total == 1
    assert passengers.get_passenger("2", passenger_repo)["id"] == "2"
    assert passengers.update_passenger(
        "2", PassengerUpdate(fare_gate=5), passenger_repo, {}
    )["fare_gate"] == 5
    assert passengers.delete_passenger("2", passenger_repo, {}).status_code == 204
    _assert_not_found(lambda: passengers.get_passenger("missing", passenger_repo))
    _assert_not_found(
        lambda: passengers.update_passenger(
            "missing", PassengerUpdate(fare_gate=5), passenger_repo, {}
        )
    )
    _assert_not_found(lambda: passengers.delete_passenger("missing", passenger_repo, {}))

    financial_repo = Crud(
        {
            "id": "3",
            "date": date(2026, 8, 1),
            "sales": 1.0,
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert financials.create_financial(
        financials.FinancialCreate(date=date(2026, 8, 1)), financial_repo, {}
    )["id"] == "3"
    assert financials.list_financials(financial_repo).meta.total == 1
    assert financials.get_financial("3", financial_repo)["id"] == "3"
    assert financials.update_financial(
        "3", FinancialUpdate(sales=5), financial_repo, {}
    )["sales"] == 5
    assert financials.delete_financial("3", financial_repo, {}).status_code == 204
    _assert_not_found(lambda: financials.get_financial("missing", financial_repo))
    _assert_not_found(
        lambda: financials.update_financial(
            "missing", FinancialUpdate(sales=5), financial_repo, {}
        )
    )
    _assert_not_found(lambda: financials.delete_financial("missing", financial_repo, {}))


def test_alert_and_preference_routes():
    alert_repo = Crud(
        {
            "id": "4",
            "date": date(2026, 8, 1),
            "type": "Teste",
            "description": "Alerta de teste",
            "severity": "critical",
            "status": "open",
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    created_alert = alerts.create_alert(
        AlertCreate(
            date=date(2026, 8, 1),
            type="Teste",
            description="Alerta de teste",
            severity=AlertSeverity.CRITICAL,
        ),
        alert_repo,
        {},
    )
    assert created_alert["type"] == "Teste"
    result = alerts.list_alerts(
        alert_repo,
        alert_status=AlertStatus.OPEN,
        severity=AlertSeverity.CRITICAL,
    )
    assert result.meta.total == 1
    assert alerts.get_alert("4", alert_repo)["id"] == "4"
    assert alerts.update_alert(
        "4", AlertUpdate(status=AlertStatus.RESOLVED), alert_repo, {}
    )["status"] == AlertStatus.RESOLVED
    assert alerts.delete_alert("4", alert_repo, {}).status_code == 204
    _assert_not_found(lambda: alerts.get_alert("missing", alert_repo))
    _assert_not_found(
        lambda: alerts.update_alert(
            "missing", AlertUpdate(status=AlertStatus.RESOLVED), alert_repo, {}
        )
    )
    _assert_not_found(lambda: alerts.delete_alert("missing", alert_repo, {}))

    class PreferenceRepo:
        def __init__(self):
            self.value = None

        def get_by_user(self, user_id):
            return self.value

        def upsert(self, user_id, data):
            self.value = {**(self.value or {}), "id": "p1", "user_id": user_id, **data}
            return self.value

    preference_repo = PreferenceRepo()
    current = {"id": "u1"}
    created = preferences.get_my_preferences(current, preference_repo)
    assert created["notify_critical_alerts"] is True
    assert created["theme"] == "system"
    assert preferences.get_my_preferences(current, preference_repo) is created
    updated = preferences.update_my_preferences(
        PreferenceUpdate(weekly_email_summary=True), current, preference_repo
    )
    assert updated["weekly_email_summary"] is True
    assert updated["notify_critical_alerts"] is True
    themed = preferences.update_my_preferences(
        PreferenceUpdate(theme="dark"), {"id": "new-user"}, PreferenceRepo()
    )
    assert themed["theme"] == "dark"
    assert themed["notify_critical_alerts"] is True


def test_user_and_auth_routes(monkeypatch):
    repository = Crud(
        {
            "id": "66f000000000000000000001",
            "nome": "Gestor",
            "email": "gestor@semob.com",
            "ativo": True,
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    monkeypatch.setattr(user, "hash_password", lambda password: "hash")
    created = user.create_user(
        UserCreate(nome="Gestor", email="GESTOR@semob.com", senha="12345678"),
        repository,
    )
    assert created["senha_hash"] == "hash"
    assert user.list_users(repository, {}, name="ges")["meta"].total == 1
    assert user.get_user(created["id"], repository, {})["id"] == created["id"]
    updated = user.update_user(
        created["id"], UserUpdate(nome="Novo gestor"), repository, {}
    )
    assert updated["nome"] == "Novo gestor"
    assert user.delete_user(created["id"], repository, {}).status_code == 204
    _assert_not_found(lambda: user.get_user("missing", repository, {}))
    _assert_not_found(
        lambda: user.update_user("missing", UserUpdate(nome="Outro"), repository, {})
    )
    _assert_not_found(lambda: user.delete_user("missing", repository, {}))

    monkeypatch.setattr(auth, "authenticate_user", lambda *args: {"id": "u1"})
    monkeypatch.setattr(auth, "create_access_token", lambda *args: "token")
    token = auth.login(UserLogin(email="gestor@semob.com", senha="senha"), repository)
    assert token.access_token == "token"
    monkeypatch.setattr(auth, "authenticate_user", lambda *args: None)
    with pytest.raises(HTTPException) as error:
        auth.login(UserLogin(email="gestor@semob.com", senha="errada"), repository)
    assert error.value.status_code == 401


def test_user_routes_normalize_email_and_return_duplicate_conflicts(monkeypatch):
    class DuplicateRepository(Crud):
        def create(self, data):
            raise DuplicateKeyError("duplicate")

        def update(self, item_id, data):
            assert data["email"] == "novo@semob.com"
            raise DuplicateKeyError("duplicate")

    repository = DuplicateRepository()
    monkeypatch.setattr(user, "hash_password", lambda password: "hash")

    with pytest.raises(HTTPException) as create_error:
        user.create_user(
            UserCreate(nome="Gestor", email="GESTOR@semob.com", senha="12345678"),
            repository,
        )
    with pytest.raises(HTTPException) as update_error:
        user.update_user(
            "u1",
            UserUpdate(email="NOVO@semob.com"),
            repository,
            {},
        )

    assert create_error.value.status_code == 409
    assert update_error.value.status_code == 409
