from __future__ import annotations

import os
from dataclasses import dataclass


def _get_env(key: str, default: str = "") -> str:
    value = os.environ.get(key, default).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


DEFAULT_COLLECTION = "governai_ontology"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class QdrantSettings:
    url: str
    api_key: str
    collection_name: str = DEFAULT_COLLECTION
    embedding_model: str = DEFAULT_EMBEDDING_MODEL

    @classmethod
    def from_env(cls) -> QdrantSettings:
        url = _get_env("QDRANT_URL")
        api_key = _get_env("QDRANT_API_KEY")
        if not url:
            raise ValueError("QDRANT_URL is required. Set it in .env or the environment.")
        if not api_key:
            raise ValueError(
                "QDRANT_API_KEY is required. Set it in .env or the environment."
            )
        return cls(
            url=url.rstrip("/"),
            api_key=api_key,
            collection_name=_get_env("QDRANT_COLLECTION", DEFAULT_COLLECTION),
            embedding_model=_get_env("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        )
