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


def test_user_lookup_and_list_normalize_search_values():
    database = MagicMock()
    database.users.find_one.return_value = {
        "_id": ObjectId(),
        "email": "gestor@example.com",
    }
    repository = user_repository.UserRepository(database)
    repository.paginate = MagicMock(return_value=([], 0))

    found = repository.get_by_email("GESTOR@EXAMPLE.COM")
    repository.list(1, 20, "Ges.tor")

    assert found["email"] == "gestor@example.com"
    database.users.find_one.assert_called_once_with({"email": "gestor@example.com"})
    query = repository.paginate.call_args.args[0]
    assert query["nome"]["$regex"] == "Ges\\.tor"
    repository.list(1, 20)
    assert repository.paginate.call_args.args[0] == {}


def test_legacy_user_helpers_delegate_to_repository(monkeypatch):
    repository = MagicMock()
    repository.create.return_value = {"id": "u1"}
    repository.list.side_effect = [([{"id": "u1"}], 1), ([{"id": "u1"}], 1)]
    repository.get.return_value = {"id": "u1"}
    repository.delete.return_value = {"id": "u1"}
    repository.update.return_value = {"id": "u1", "nome": "Novo"}
    repository.get_by_email.return_value = {"id": "u1"}
    monkeypatch.setattr(user_repository, "_repository", lambda: repository)

    assert user_repository.create_user({"nome": "Gestor"}) == "u1"
    assert user_repository.get_users()[0]["id"] == "u1"
    assert user_repository.get_user_by_id("u1")["id"] == "u1"
    assert user_repository.get_users_by_name("Ges")[0]["id"] == "u1"
    assert user_repository.delete_user_by_id("u1")["id"] == "u1"
    assert user_repository.update_user_by_id("u1", {"nome": "Novo"})["nome"] == "Novo"
    assert user_repository.get_user_by_email("gestor@example.com")["id"] == "u1"
