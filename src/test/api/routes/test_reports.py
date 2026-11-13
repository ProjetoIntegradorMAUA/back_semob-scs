from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from src.app.api.dependencies import (
    get_alert_repository,
    get_current_user,
    get_financial_repository,
    get_operation_repository,
    get_passenger_repository,
    get_report_repository,
)
from src.app.core.config import get_settings
from src.app.main import app
from src.app.services.report_service import ReportService


NOW = datetime.now(timezone.utc)
USER = {"id": "66f000000000000000000001", "ativo": True}


class Series:
    def __init__(self, rows):
        self.rows = rows

    def find_range(self, start_date, end_date):
        return self.rows


class Alerts(Series):
    def count_open(self, start_date, end_date):
        return len(self.rows)


class Reports:
    def __init__(self):
        self.items = {}
        self.failed = False

    def create(self, data):
        item = {
            "id": "66f000000000000000000099",
            **data,
            "created_at": NOW,
            "updated_at": NOW,
        }
        self.items[item["id"]] = item
        return item

    def update(self, report_id, data):
        self.items[report_id].update(data)
        self.items[report_id]["updated_at"] = NOW
        self.failed = data.get("status") == "failed"
        return self.items[report_id]

    def get(self, report_id):
        return self.items.get(report_id)

    def list_for_user(self, user_id, page, page_size):
        items = [item for item in self.items.values() if item["requested_by"] == user_id]
        return items, len(items)

    def delete(self, report_id):
        return self.items.pop(report_id, None)


def _override(reports):
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_report_repository] = lambda: reports
    app.dependency_overrides[get_operation_repository] = lambda: Series(
        [{"date": date(2026, 8, 1), "scheduled_trips": 10, "completed_trips": 9}]
    )
    app.dependency_overrides[get_passenger_repository] = lambda: Series([])
    app.dependency_overrides[get_financial_repository] = lambda: Series([])
    app.dependency_overrides[get_alert_repository] = lambda: Alerts([])


def test_report_lifecycle_generates_downloads_lists_and_deletes(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "report_output_dir", str(tmp_path))
    reports = Reports()
    _override(reports)
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/reports",
                json={
                    "report_type": "operations",
                    "format": "csv",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-31",
                },
            )
            report_id = created.json()["id"]
            listed = client.get("/api/v1/reports")
            detail = client.get(f"/api/v1/reports/{report_id}")
            downloaded = client.get(f"/api/v1/reports/{report_id}/download")
            deleted = client.delete(f"/api/v1/reports/{report_id}")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["status"] == "completed"
    assert listed.json()["meta"]["total"] == 1
    assert detail.status_code == 200
    assert downloaded.status_code == 200
    assert b"scheduled_trips" in downloaded.content
    assert deleted.status_code == 204
    assert not list(tmp_path.iterdir())


def test_report_generation_failure_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "report_output_dir", str(tmp_path))
    monkeypatch.setattr(
        ReportService,
        "generate",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("erro")),
    )
    reports = Reports()
    _override(reports)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/reports",
                json={
                    "report_type": "operations",
                    "format": "csv",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-31",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert reports.failed is True


def test_report_access_and_file_state_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "report_output_dir", str(tmp_path))
    reports = Reports()
    pending = reports.create(
        {
            "requested_by": USER["id"],
            "report_type": "operations",
            "format": "csv",
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 31),
            "status": "pending",
            "file_url": None,
            "file_name": None,
            "content_type": None,
            "error_message": None,
        }
    )
    _override(reports)
    try:
        with TestClient(app) as client:
            unavailable = client.get(f"/api/v1/reports/{pending['id']}/download")
            reports.update(
                pending["id"],
                {"status": "completed", "file_name": "ausente.csv"},
            )
            gone = client.get(f"/api/v1/reports/{pending['id']}/download")
            missing = client.get("/api/v1/reports/66f000000000000000000088")
            missing_download = client.get(
                "/api/v1/reports/66f000000000000000000088/download"
            )
            missing_delete = client.delete("/api/v1/reports/66f000000000000000000088")
    finally:
        app.dependency_overrides.clear()

    assert unavailable.status_code == 409
    assert gone.status_code == 410
    assert missing.status_code == 404
    assert missing_download.status_code == 404
    assert missing_delete.status_code == 404
