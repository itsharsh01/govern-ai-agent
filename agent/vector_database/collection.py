from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models

PAYLOAD_KEYWORD_INDEX_FIELDS = ("node_type", "name")


def ensure_payload_indexes(client: QdrantClient, collection_name: str) -> None:
    """Create keyword indexes required for ontology search filters."""
    if not client.collection_exists(collection_name):
        return
    for field_name in PAYLOAD_KEYWORD_INDEX_FIELDS:
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:
            message = str(exc).lower()
            if "already exists" in message or "already has index" in message:
                continue
            raise


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    *,
    recreate: bool = False,
) -> None:
    exists = client.collection_exists(collection_name)

    if exists and not recreate:
        info = client.get_collection(collection_name)
        current_size = info.config.params.vectors.size  # type: ignore[union-attr]
        if current_size != vector_size:
            raise ValueError(
                f"Collection '{collection_name}' has vector size {current_size}, "
                f"but model requires {vector_size}. Re-run with --recreate."
            )
        ensure_payload_indexes(client, collection_name)
        return

    if exists and recreate:
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )
    ensure_payload_indexes(client, collection_name)
