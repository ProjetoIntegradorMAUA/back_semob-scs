from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.app.api.dependencies import get_operation_repository
from src.app.main import app


class FakeOperationRepository:
    def list(self, page, page_size, start_date, end_date, line_code):
        now = datetime.now(timezone.utc)
        return (
            [
                {
                    "id": "66f000000000000000000001",
                    "date": "2026-08-01",
                    "line_code": None,
                    "vehicles_operated": 37,
                    "max_vehicles_in_service": 35,
                    "scheduled_trips": 924,
                    "completed_trips": 920,
                    "productive_km": 6889.4,
                    "deadhead_km": 344.3,
                    "source": "smart_report",
                    "created_at": now,
                    "updated_at": now,
                }
            ],
            1,
        )


def test_list_operations_uses_repository_dependency():
    app.dependency_overrides[get_operation_repository] = lambda: FakeOperationRepository()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/operations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["missing_trips"] == 4
    assert body["items"][0]["total_km"] == 7233.7
