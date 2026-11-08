from pymongo import DESCENDING
from pymongo.database import Database

from src.app.repositories.base import CrudRepository


class ImportJobRepository(CrudRepository):
    def __init__(self, database: Database):
        super().__init__(database.import_jobs)

    def list_for_user(self, user_id: str, page: int, page_size: int):
        return self.paginate(
            {"requested_by": user_id}, page, page_size, [("created_at", DESCENDING)]
        )

    def get_for_user(self, import_id: str, user_id: str):
        item = self.get(import_id)
        if item is None or item.get("requested_by") != user_id:
            return None
        return item
