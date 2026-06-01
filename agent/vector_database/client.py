from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from qdrant_client import QdrantClient

from .config import QdrantSettings

_client: QdrantClient | None = None


def create_client(settings: QdrantSettings | None = None) -> QdrantClient:
    """Create a Qdrant client from settings or environment."""
    settings = settings or QdrantSettings.from_env()
    return QdrantClient(url=settings.url, api_key=settings.api_key)


def get_client(*, reset: bool = False) -> QdrantClient:
    """Return a shared Qdrant client (singleton)."""
    global _client
    if _client is None or reset:
        _client = create_client()
    return _client


@contextmanager
def qdrant_client(settings: QdrantSettings | None = None) -> Iterator[QdrantClient]:
    """Context manager that closes the client when done."""
    client = create_client(settings)
    try:
        yield client
    finally:
        client.close()


def verify_connection(settings: QdrantSettings | None = None) -> dict:
    """Ping Qdrant and return cluster info."""
    settings = settings or QdrantSettings.from_env()
    with qdrant_client(settings) as client:
        collections = client.get_collections()
        return {
            "url": settings.url,
            "collection_name": settings.collection_name,
            "collections": [c.name for c in collections.collections],
            "connected": True,
        }
