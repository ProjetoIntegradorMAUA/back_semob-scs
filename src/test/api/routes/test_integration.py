from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from src.app.api.dependencies import (
    get_alert_repository,
    get_current_user,
    get_financial_repository,
    get_hourly_operation_repository,
    get_operation_repository,
    get_passenger_repository,
)
from src.app.main import app


NOW = datetime.now(timezone.utc)
USER = {"id": "66f000000000000000000001", "email": "gestor@semob.test", "ativo": True}


class FakeOperationRepository:
    def __init__(self, rows=None):
        self.imported = []
        self.rows = rows or [
            {
                "date": datetime(2026, 8, 1),
                "line_code": None,
                "scheduled_trips": 100,
                "completed_trips": 98,
                "productive_km": 700,
                "deadhead_km": 20,
            }
        ]

    def create(self, data):
        return {
            "id": "66f000000000000000000010",
            **data,
            "created_at": NOW,
            "updated_at": NOW,
        }

    def find_range(self, start_date, end_date):
        return self.rows

    def upsert_many(self, rows):
        self.imported = rows
        return len(rows)


class FakeSeriesRepository:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.imported = []

    def find_range(self, start_date, end_date):
        return self.rows

    def upsert_many(self, rows):
        self.imported = rows
        return len(rows)


class FakeAlertRepository:
    def __init__(self):
        self.generated = []

    def count_open(self, start_date, end_date):
        return 3

    def upsert_generated(self, item):
        self.generated.append(item)
        return True

    def resolve_stale_generated(self, start_date, end_date, active_keys):
        return 0


def _override_dashboard_dependencies():
    operations = FakeOperationRepository()
    passengers = FakeSeriesRepository(
        [{"date": datetime(2026, 8, 1), "fare_gate": 10, "prepaid": 5, "non_paying": 20}]
    )
    financials = FakeSeriesRepository(
        [{"date": datetime(2026, 8, 1), "sales": 1000, "usage": 750}]
    )
    app.dependency_overrides[get_operation_repository] = lambda: operations
    app.dependency_overrides[get_passenger_repository] = lambda: passengers
    app.dependency_overrides[get_financial_repository] = lambda: financials
    app.dependency_overrides[get_alert_repository] = lambda: FakeAlertRepository()
    return operations, passengers, financials


def test_protected_write_rejects_missing_token():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/operations",
            json={"date": "2026-08-01", "scheduled_trips": 10, "completed_trips": 9},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido ou expirado."


def test_authenticated_operation_creation_computes_response_fields():
    operations = FakeOperationRepository()
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_operation_repository] = lambda: operations
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/operations",
                json={
                    "date": "2026-08-01",
                    "scheduled_trips": 100,
                    "completed_trips": 98,
                    "productive_km": 700,
                    "deadhead_km": 20,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["missing_trips"] == 2
    assert response.json()["total_km"] == 720


def test_dashboard_overview_integration():
    _override_dashboard_dependencies()
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/dashboard/overview",
                params={"start_date": "2026-08-01", "end_date": "2026-08-31"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    totals = response.json()["totals"]
    assert totals["passengers"] == 35
    assert totals["completion_rate"] == 98
    assert totals["circulating_credit"] == 250
    assert totals["open_alerts"] == 3


def test_dashboard_rejects_inverted_period():
    _override_dashboard_dependencies()
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/dashboard/overview",
                params={"start_date": "2026-09-01", "end_date": "2026-08-01"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "Período inválido."


def test_smart_report_upload_parses_and_upserts():
    operations, passengers, financials = _override_dashboard_dependencies()
    app.dependency_overrides[get_current_user] = lambda: USER
    content = b"""
    <table><th>Data</th><th>diaSem</th><th>nrVeiculos</th><th>nrMaxVeicFx</th>
    <th>nrViagensProgr</th><th>nrViagensRealiz</th><th>kmProd</th><th>kmImprod</th>
    <tr><td>01/08/2026</td><td>Sab</td><td>37</td><td>35</td><td>924</td>
    <td>920</td><td>6889,4</td><td>344,3</td></tr></table>
    """
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/imports/smart-report",
                data={"report_type": "operations"},
                files={"file": ("Mensal_202608.html", content, "text/html")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["parsed"] == 1
    assert len(operations.imported) == 1
    assert passengers.imported == []
    assert financials.imported == []


def test_smart_report_upload_rejects_unknown_html():
    _override_dashboard_dependencies()
    app.dependency_overrides[get_current_user] = lambda: USER
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/imports/smart-report",
                data={"report_type": "operations"},
                files={"file": ("invalido.html", b"<html></html>", "text/html")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "Tabela esperada" in response.json()["detail"]


def test_smart_data_batch_upserts_all_series_and_forces_source():
    operations = FakeOperationRepository()
    passengers = FakeSeriesRepository([])
    financials = FakeSeriesRepository([])
    hourly = FakeSeriesRepository([])
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_operation_repository] = lambda: operations
    app.dependency_overrides[get_passenger_repository] = lambda: passengers
    app.dependency_overrides[get_financial_repository] = lambda: financials
    app.dependency_overrides[get_hourly_operation_repository] = lambda: hourly
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/imports/smart-data",
                json={
                    "operations": [
                        {"date": "2026-08-01", "scheduled_trips": 10}
                    ],
                    "passengers": [{"date": "2026-08-01", "fare_gate": 20}],
                    "financials": [{"date": "2026-08-01", "sales": 30}],
                    "hourly_operations": [
                        {"date": "2026-08-01", "hour": 4, "trips": 5}
                    ],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 4
    assert operations.imported[0]["source"] == "smart_data_api"
    assert passengers.imported[0]["source"] == "smart_data_api"
    assert financials.imported[0]["source"] == "smart_data_api"
    assert hourly.imported[0]["source"] == "smart_data_api"


def test_generate_alerts_endpoint_detects_anomaly():
    operations = FakeOperationRepository(
        [
            {
                "date": datetime(2026, 8, 1),
                "line_code": "01",
                "scheduled_trips": 100,
                "completed_trips": 90,
                "productive_km": 980,
                "deadhead_km": 20,
            }
        ]
    )
    financials = FakeSeriesRepository([])
    alerts = FakeAlertRepository()
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_operation_repository] = lambda: operations
    app.dependency_overrides[get_financial_repository] = lambda: financials
    app.dependency_overrides[get_alert_repository] = lambda: alerts
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/alerts/generate",
                params={"start_date": "2026-08-01", "end_date": "2026-08-31"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["candidates"] == 1
    assert response.json()["created"] == 1
    assert alerts.generated[0]["rule_code"] == "trip_completion_low"


def test_generate_alerts_endpoint_rejects_inverted_period():
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_operation_repository] = FakeOperationRepository
    app.dependency_overrides[get_financial_repository] = lambda: FakeSeriesRepository([])
    app.dependency_overrides[get_alert_repository] = FakeAlertRepository
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/alerts/generate",
                params={"start_date": "2026-08-31", "end_date": "2026-08-01"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "Período inválido."
