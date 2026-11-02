from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pymongo import ASCENDING, UpdateOne
from pymongo.database import Database

from src.app.models.common import utc_now
from src.app.repositories.base import CrudRepository, mongo_ready, serialize_document


def date_filter(start_date: date | None, end_date: date | None) -> dict[str, Any]:
    if start_date is None and end_date is None:
        return {}
    value: dict[str, Any] = {}
    if start_date is not None:
        value["$gte"] = datetime.combine(start_date, datetime.min.time())
    if end_date is not None:
        value["$lte"] = datetime.combine(end_date, datetime.max.time())
    return {"date": value}


class TimeSeriesRepository(CrudRepository):
    collection_name: str
    unique_fields: tuple[str, ...] = ("date",)

    def __init__(self, database: Database):
        super().__init__(database[self.collection_name])

    def list(
        self,
        page: int,
        page_size: int,
        start_date: date | None = None,
        end_date: date | None = None,
        extra_query: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = date_filter(start_date, end_date)
        query.update(extra_query or {})
        return self.paginate(query, page, page_size, [("date", ASCENDING)])

    def find_range(
        self,
        start_date: date,
        end_date: date,
        extra_query: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query = date_filter(start_date, end_date)
        query.update(extra_query or {})
        documents = self.collection.find(query).sort("date", ASCENDING)
        return [
            item
            for item in (serialize_document(document) for document in documents)
            if item is not None
        ]

    def upsert_many(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        now = utc_now()
        operations = []
        for row in rows:
            match = {field: row.get(field) for field in self.unique_fields}
            operations.append(
                UpdateOne(
                    match,
                    {
                        "$set": mongo_ready({**row, "updated_at": now}),
                        "$setOnInsert": {"created_at": now},
                    },
                    upsert=True,
                )
            )
        self.collection.bulk_write(operations, ordered=False)
        return len(operations)
