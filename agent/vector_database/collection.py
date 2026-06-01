from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models


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
