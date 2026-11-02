from unittest.mock import MagicMock

from bson import ObjectId

from src.app.repositories import user_repository


def test_create_user_normalizes_email():
    database = MagicMock()
    database.users.insert_one.return_value.inserted_id = ObjectId()
    repository = user_repository.UserRepository(database)

    created = repository.create(
        {"nome": "Gestor", "email": "GESTOR@EXAMPLE.COM", "senha_hash": "hash"}
    )

    inserted = database.users.insert_one.call_args.args[0]
    assert inserted["email"] == "gestor@example.com"
    assert created["id"]


def test_get_invalid_id_does_not_query_database():
    database = MagicMock()
    repository = user_repository.UserRepository(database)

    assert repository.get("id-invalido") is None
    database.users.find_one.assert_not_called()
