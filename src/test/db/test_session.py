from unittest.mock import MagicMock

from src.app.db import session


def test_database_client_lifecycle_and_ping(monkeypatch):
    settings = MagicMock(
        mongo_uri="mongodb://example:27017",
        mongo_database="semob_test",
    )
    mongo_client = MagicMock()
    database = MagicMock()
    mongo_client.__getitem__.return_value = database
    constructor = MagicMock(return_value=mongo_client)
    monkeypatch.setattr(session, "get_settings", lambda: settings)
    monkeypatch.setattr(session, "MongoClient", constructor)
    session.get_client.cache_clear()

    try:
        assert session.get_client() is mongo_client
        assert session.get_database() is database
        assert session.ping_database() is True
        assert session.client["legacy"] is mongo_client["legacy"]
        session.close_database()
        mongo_client.close.assert_called_once()
        assert session.get_client.cache_info().currsize == 0
    finally:
        session.get_client.cache_clear()


def test_database_ping_failure_and_close_without_cached_client(monkeypatch):
    failing = MagicMock()
    failing.admin.command.side_effect = RuntimeError("offline")
    monkeypatch.setattr(session, "get_client", MagicMock(return_value=failing))

    assert session.ping_database() is False
    session.get_client.cache_info.return_value.currsize = 0
    session.close_database()
    failing.close.assert_not_called()
