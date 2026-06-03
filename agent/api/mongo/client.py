from __future__ import annotations

from typing import Any

import certifi
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .config import MongoSettings

_client: MongoClient | None = None
_settings: MongoSettings | None = None


def connect_mongo(settings: MongoSettings | None = None) -> None:
    global _client, _settings
    _settings = settings or MongoSettings.from_env()
    kwargs: dict[str, Any] = {"serverSelectionTimeoutMS": 10000}
    if _settings.uri.startswith("mongodb+srv://") or "tls=true" in _settings.uri.lower():
        kwargs["tlsCAFile"] = certifi.where()
    _client = MongoClient(_settings.uri, **kwargs)
    _client.admin.command("ping")


def close_mongo() -> None:
    global _client, _settings
    if _client is not None:
        _client.close()
    _client = None
    _settings = None


def get_client() -> MongoClient:
    if _client is None:
        connect_mongo()
    assert _client is not None
    return _client


def get_settings() -> MongoSettings:
    if _settings is None:
        connect_mongo()
    assert _settings is not None
    return _settings


def get_database() -> Database:
    settings = get_settings()
    return get_client()[settings.database_name]


def get_customers_collection() -> Collection:
    settings = get_settings()
    return get_database()[settings.collection_name]


def verify_connection() -> dict[str, Any]:
    connect_mongo()
    settings = _settings or MongoSettings.from_env()
    collection = get_customers_collection()
    return {
        "connected": True,
        "database": settings.database_name,
        "collection": settings.collection_name,
        "document_count": collection.count_documents({}),
    }
