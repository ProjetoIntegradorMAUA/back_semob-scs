from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from src.app.api.dependencies import get_current_user, get_hourly_operation_repository
from src.app.main import app


NOW = datetime.now(timezone.utc)
USER = {"id": "66f000000000000000000001", "ativo": True}


class HourlyOperations:
    def __init__(self):
        self.items = {}
        self.next_id = 1

    def create(self, data):
        item = {
            "id": f"66f0000000000000000000{self.next_id:02d}",
            **data,
            "created_at": NOW,
            "updated_at": NOW,
        }
        self.next_id += 1
        self.items[item["id"]] = item
        return item

    def list(self, page, page_size, start_date, end_date, line_code):
        items = list(self.items.values())
        if line_code is not None:
            items = [item for item in items if item["line_code"] == line_code]
        return items, len(items)

    def get(self, operation_id):
        return self.items.get(operation_id)

    def update(self, operation_id, data):
        item = self.items.get(operation_id)
        if item is not None:
            item.update(data)
        return item

    def delete(self, operation_id):
        return self.items.pop(operation_id, None)


def test_hourly_operation_crud_and_filters():
    repository = HourlyOperations()
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_hourly_operation_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/hourly-operations",
                json={
                    "date": "2026-08-01",
                    "hour": 7,
                    "line_code": "01",
                    "vehicles": 12,
                    "trips": 18,
                },
            )
            operation_id = created.json()["id"]
            listed = client.get(
                "/api/v1/hourly-operations",
                params={
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-31",
                    "line_code": "01",
                },
            )
            detail = client.get(f"/api/v1/hourly-operations/{operation_id}")
            updated = client.patch(
                f"/api/v1/hourly-operations/{operation_id}",
                json={"vehicles": 14},
            )
            deleted = client.delete(f"/api/v1/hourly-operations/{operation_id}")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["source"] == "manual"
    assert listed.json()["meta"]["total"] == 1
    assert detail.json()["trips"] == 18
    assert updated.json()["vehicles"] == 14
    assert deleted.status_code == 204


def test_hourly_operation_not_found_and_write_authentication():
    repository = HourlyOperations()
    app.dependency_overrides[get_hourly_operation_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            unauthenticated = client.post(
                "/api/v1/hourly-operations",
                json={"date": "2026-08-01", "hour": 7},
            )
            missing = client.get(
                "/api/v1/hourly-operations/66f000000000000000000099"
            )

        app.dependency_overrides[get_current_user] = lambda: USER
        with TestClient(app) as client:
            missing_update = client.patch(
                "/api/v1/hourly-operations/66f000000000000000000099",
                json={"trips": 1},
            )
            missing_delete = client.delete(
                "/api/v1/hourly-operations/66f000000000000000000099"
            )
    finally:
        app.dependency_overrides.clear()

    assert unauthenticated.status_code == 401
    assert missing.status_code == 404
    assert missing_update.status_code == 404
    assert missing_delete.status_code == 404


def test_hourly_operation_contract_rejects_invalid_hour_and_empty_patch():
    repository = HourlyOperations()
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_hourly_operation_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            invalid_hour = client.post(
                "/api/v1/hourly-operations",
                json={"date": str(date(2026, 8, 1)), "hour": 24},
            )
            empty_patch = client.patch(
                "/api/v1/hourly-operations/66f000000000000000000099",
                json={},
            )
    finally:
        app.dependency_overrides.clear()

    assert invalid_hour.status_code == 422
    assert empty_patch.status_code == 422


def test_hourly_operation_natural_key_conflicts_return_409():
    repository = HourlyOperations()
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_hourly_operation_repository] = lambda: repository
    repository.create = lambda data: (_ for _ in ()).throw(DuplicateKeyError("duplicate"))
    try:
        with TestClient(app) as client:
            duplicate_create = client.post(
                "/api/v1/hourly-operations",
                json={"date": "2026-08-01", "hour": 7, "line_code": "01"},
            )
            repository.update = lambda operation_id, data: (
                _ for _ in ()
            ).throw(DuplicateKeyError("duplicate"))
            duplicate_update = client.patch(
                "/api/v1/hourly-operations/66f000000000000000000099",
                json={"hour": 8},
            )
    finally:
        app.dependency_overrides.clear()

    assert duplicate_create.status_code == 409
    assert duplicate_update.status_code == 409
    assert "data, hora e linha" in duplicate_create.json()["detail"]
