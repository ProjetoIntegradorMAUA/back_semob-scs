from typing import Any

from pymongo import ReturnDocument
from pymongo.database import Database

from src.app.models.common import utc_now
from src.app.repositories.base import CrudRepository, serialize_document


class PreferenceRepository(CrudRepository):
    def __init__(self, database: Database):
        super().__init__(database.preferences)

    def get_by_user(self, user_id: str) -> dict[str, Any] | None:
        return serialize_document(self.collection.find_one({"user_id": user_id}))

    def upsert(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        document = self.collection.find_one_and_update(
            {"user_id": user_id},
            {
                "$set": {**data, "user_id": user_id, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(document)  # type: ignore[return-value]
