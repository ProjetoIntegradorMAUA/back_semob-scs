from datetime import date, datetime
from typing import Any

from pymongo import DESCENDING
from pymongo.database import Database

from src.app.models.common import AlertSeverity, AlertStatus, utc_now
from src.app.repositories.base import CrudRepository, mongo_ready
from src.app.repositories.time_series_repository import date_filter


class AlertRepository(CrudRepository):
    def __init__(self, database: Database):
        super().__init__(database.alerts)

    def list(
        self,
        page: int,
        page_size: int,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
    ):
        query = date_filter(start_date, end_date)
        if status:
            query["status"] = status.value
        if severity:
            query["severity"] = severity.value
        return self.paginate(query, page, page_size, [("date", DESCENDING)])

    def count_open(self, start_date: date, end_date: date) -> int:
        query = date_filter(start_date, end_date)
        query["status"] = {"$ne": AlertStatus.RESOLVED.value}
        return self.collection.count_documents(query)

    def upsert_generated(self, data: dict[str, Any]) -> bool:
        """Persiste um alerta automático sem reabrir ocorrências já resolvidas."""

        now = utc_now()
        key = mongo_ready(
            {
                "rule_code": data["rule_code"],
                "date": data["date"],
                "line_code": data.get("line_code"),
            }
        )
        payload = {
            field: value for field, value in data.items() if field != "status"
        }
        result = self.collection.update_one(
            key,
            {
                "$set": mongo_ready({**payload, "updated_at": now}),
                "$setOnInsert": {
                    "created_at": now,
                    "status": AlertStatus.OPEN.value,
                },
            },
            upsert=True,
        )
        return result.upserted_id is not None

    def resolve_stale_generated(
        self,
        start_date: date,
        end_date: date,
        active_keys: set[tuple[str, str, str]],
    ) -> int:
        """Resolve alertas automáticos cuja anomalia não aparece mais no período."""

        query = date_filter(start_date, end_date)
        query["rule_code"] = {"$type": "string"}
        query["status"] = {"$ne": AlertStatus.RESOLVED.value}
        stale_ids = []
        for document in self.collection.find(
            query, {"rule_code": 1, "date": 1, "line_code": 1}
        ):
            value = document["date"]
            day = value.date() if isinstance(value, datetime) else value
            key = (
                str(document["rule_code"]),
                day.isoformat(),
                document.get("line_code") or "",
            )
            if key not in active_keys:
                stale_ids.append(document["_id"])

        if not stale_ids:
            return 0
        result = self.collection.update_many(
            {"_id": {"$in": stale_ids}},
            {
                "$set": {
                    "status": AlertStatus.RESOLVED.value,
                    "updated_at": utc_now(),
                }
            },
        )
        return result.modified_count
