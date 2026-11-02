from pymongo import DESCENDING
from pymongo.database import Database

from src.app.repositories.base import CrudRepository


class ReportRepository(CrudRepository):
    def __init__(self, database: Database):
        super().__init__(database.report_jobs)

    def list_for_user(self, user_id: str, page: int, page_size: int):
        return self.paginate(
            {"requested_by": user_id}, page, page_size, [("created_at", DESCENDING)]
        )
