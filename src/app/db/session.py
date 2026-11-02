from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi

from src.app.core.config import get_settings


@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(
        settings.mongo_uri,
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=3000,
        connect=False,
    )


def get_database() -> Database:
    settings = get_settings()
    return get_client()[settings.mongo_database]


def ping_database() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except Exception:
        return False


def close_database() -> None:
    if get_client.cache_info().currsize:
        get_client().close()
        get_client.cache_clear()


class _LazyClient:
    """Compatibilidade temporária com módulos antigos que importavam ``client``."""

    def __getitem__(self, name: str):
        return get_client()[name]


client = _LazyClient()
