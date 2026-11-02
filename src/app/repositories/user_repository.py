import re
from typing import Any

from pymongo import ASCENDING
from pymongo.database import Database

from src.app.repositories.base import CrudRepository, serialize_document


class UserRepository(CrudRepository):
    def __init__(self, database: Database):
        super().__init__(database.users)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        return super().create({**data, "email": data["email"].lower()})

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        return serialize_document(self.collection.find_one({"email": email.lower()}))

    def list(
        self, page: int, page_size: int, name: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        query = {"nome": {"$regex": re.escape(name), "$options": "i"}} if name else {}
        return self.paginate(query, page, page_size, [("nome", ASCENDING)])


def _repository() -> UserRepository:
    from src.app.db.session import get_database

    return UserRepository(get_database())


def create_user(dados: dict):
    return _repository().create(dados)["id"]


def get_users():
    return _repository().list(1, 100)[0]


def get_user_by_id(user_id: str):
    return _repository().get(user_id)


def get_users_by_name(name: str):
    return _repository().list(1, 100, name)[0]


def delete_user_by_id(user_id: str):
    return _repository().delete(user_id)


def update_user_by_id(user_id: str, dados: dict):
    return _repository().update(user_id, dados)


def get_user_by_email(email: str):
    return _repository().get_by_email(email)
