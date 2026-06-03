from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote_plus


def _get_env(key: str, default: str = "") -> str:
    value = os.environ.get(key, default).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


def _get_env_any(*keys: str, default: str = "") -> str:
    for key in keys:
        value = _get_env(key)
        if value:
            return value
    return default


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database_name: str
    collection_name: str = "customers"

    @classmethod
    def from_env(cls) -> MongoSettings:
        database_name = _get_env_any("MONGO_DB_NAME", "MONGODB_DATABASE", default="govern-ai-agent")
        collection_name = _get_env("MONGO_DB_COLLECTION", "customers")

        host = _get_env_any("MONGO_DB_HOST", "MONOGO_DB_HOST", "MONGODB_URI")
        if not host:
            raise ValueError(
                "MONGO_DB_HOST (or MONGODB_URI) is required. "
                "Use a full mongodb+srv:// connection string."
            )
        if host.startswith("mongodb"):
            uri = host.rstrip("/")
        else:
            user = _get_env_any("MONGO_DB_USER", "MONGODB_USER")
            password = _get_env_any(
                "MONGO_DB_PASSWORD",
                "MONOG_DB_PASSWORD",
                "MONGODB_PASSWORD",
            )
            if not user or not password:
                raise ValueError(
                    "Set MONGO_DB_HOST to a full mongodb+srv:// URI, or set "
                    "MONGO_DB_USER and MONGO_DB_PASSWORD with a hostname in MONGO_DB_HOST"
                )
            uri = (
                f"mongodb+srv://{quote_plus(user)}:{quote_plus(password)}"
                f"@{host.rstrip('/')}/"
            )

        return cls(
            uri=uri,
            database_name=database_name,
            collection_name=collection_name,
        )
