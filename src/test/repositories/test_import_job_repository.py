from unittest.mock import MagicMock, patch

from src.app.repositories.import_job_repository import ImportJobRepository


def test_list_for_user_filters_owner_and_orders_newest_first():
    database = MagicMock()
    repository = ImportJobRepository(database)

    with patch.object(repository, "paginate", return_value=([], 0)) as paginate:
        items, total = repository.list_for_user("user-1", 2, 10)

    assert items == []
    assert total == 0
    assert paginate.call_args.args[:3] == ({"requested_by": "user-1"}, 2, 10)
    assert paginate.call_args.args[3] == [("created_at", -1)]


def test_get_for_user_hides_other_users_imports():
    repository = ImportJobRepository(MagicMock())
    repository.get = MagicMock(return_value={"id": "import-1", "requested_by": "user-2"})

    assert repository.get_for_user("import-1", "user-1") is None
    repository.get.return_value = {"id": "import-1", "requested_by": "user-1"}
    assert repository.get_for_user("import-1", "user-1")["id"] == "import-1"
    repository.get.return_value = None
    assert repository.get_for_user("missing", "user-1") is None
