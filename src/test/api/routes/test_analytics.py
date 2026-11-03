from datetime import date

from fastapi.testclient import TestClient

from src.app.api.dependencies import (
    get_financial_repository,
    get_hourly_operation_repository,
    get_operation_repository,
    get_passenger_repository,
)
from src.app.main import app


class Series:
    def __init__(self, rows):
        self.rows = rows

    def find_range(self, start_date, end_date):
        return self.rows


def _override():
    app.dependency_overrides[get_operation_repository] = lambda: Series(
        [
            {
                "date": date(2026, 8, 1),
                "scheduled_trips": 10,
                "completed_trips": 9,
                "productive_km": 100,
                "deadhead_km": 5,
            }
        ]
    )
    app.dependency_overrides[get_passenger_repository] = lambda: Series(
        [{"date": date(2026, 8, 1), "fare_gate": 10, "prepaid": 2, "non_paying": 3}]
    )
    app.dependency_overrides[get_financial_repository] = lambda: Series(
        [{"date": date(2026, 8, 1), "sales": 100, "usage": 80}]
    )
    app.dependency_overrides[get_hourly_operation_repository] = lambda: Series(
        [{"date": date(2026, 8, 1), "hour": 4, "vehicles": 2, "trips": 3}]
    )


def test_all_analytics_endpoints_supply_frontend_contracts():
    _override()
    try:
        with TestClient(app) as client:
            params = {"start_date": "2026-08-01", "end_date": "2026-08-31"}
            operations = client.get("/api/v1/analytics/operations", params=params)
            passengers = client.get("/api/v1/analytics/passengers", params=params)
            financials = client.get("/api/v1/analytics/financials", params=params)
    finally:
        app.dependency_overrides.clear()

    assert operations.status_code == 200
    assert operations.json()["totals"]["missing"] == 1
    assert passengers.json()["totals"]["total"] == 15
    assert passengers.json()["hourly_supply"][0]["hour"] == 4
    assert financials.json()["totals"]["circulating_credit"] == 20


def test_analytics_rejects_inverted_period():
    _override()
    try:
        with TestClient(app) as client:
            params = {"start_date": "2026-09-01", "end_date": "2026-08-01"}
            responses = [
                client.get("/api/v1/analytics/operations", params=params),
                client.get("/api/v1/analytics/passengers", params=params),
                client.get("/api/v1/analytics/financials", params=params),
            ]
    finally:
        app.dependency_overrides.clear()

    assert all(response.status_code == 422 for response in responses)
