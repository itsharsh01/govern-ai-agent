from __future__ import annotations

import uuid
from typing import Any

from qdrant_client.http import models

from agent.knowledge_graph.client import neo4j_session
from agent.knowledge_graph.config import Neo4jSettings

from .client import qdrant_client
from .config import QdrantSettings
from .embedder import DEFAULT_MODEL, embed_texts, embedding_dimension
from .collection import ensure_collection
from .text_builder import build_embedding_text, primary_label

NODE_QUERY = """
MATCH (n:OntologyNode)
RETURN elementId(n) AS id,
       labels(n) AS labels,
       properties(n) AS props
"""


def _point_id(neo4j_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, neo4j_id))


def fetch_ontology_nodes(settings: Neo4jSettings | None = None) -> list[dict[str, Any]]:
    settings = settings or Neo4jSettings.from_env()
    nodes: list[dict[str, Any]] = []

    with neo4j_session(settings) as session:
        for record in session.run(NODE_QUERY):
            labels = list(record["labels"] or [])
            props = dict(record["props"] or {})
            nodes.append(
                {
                    "neo4j_id": record["id"],
                    "labels": labels,
                    "node_type": primary_label(labels),
                    "name": props.get("name", "(unnamed)"),
                    "category": props.get("category"),
                    "risk": props.get("risk"),
                    "props": props,
                    "embedding_text": build_embedding_text(labels, props),
                }
            )

    return nodes


def index_ontology_nodes(
    *,
    qdrant_settings: QdrantSettings | None = None,
    neo4j_settings: Neo4jSettings | None = None,
    model_name: str = DEFAULT_MODEL,
    recreate: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    qdrant_settings = qdrant_settings or QdrantSettings.from_env()
    nodes = fetch_ontology_nodes(neo4j_settings)

    if dry_run:
        return {
            "dry_run": True,
            "count": len(nodes),
            "samples": [n["embedding_text"][:300] for n in nodes[:3]],
        }

    texts = [n["embedding_text"] for n in nodes]
    vectors = embed_texts(texts, model_name=model_name)
    vector_size = embedding_dimension(model_name)

    points = [
        models.PointStruct(
            id=_point_id(node["neo4j_id"]),
            vector=vector,
            payload={
                "neo4j_id": node["neo4j_id"],
                "name": node["name"],
                "node_type": node["node_type"],
                "category": node["category"],
                "risk": node["risk"],
                "embedding_text": node["embedding_text"],
            },
        )
        for node, vector in zip(nodes, vectors, strict=True)
    ]

    with qdrant_client(qdrant_settings) as client:
        ensure_collection(
            client,
            qdrant_settings.collection_name,
            vector_size,
            recreate=recreate,
        )
        client.upsert(collection_name=qdrant_settings.collection_name, points=points)

    return {
        "indexed": len(points),
        "collection": qdrant_settings.collection_name,
        "model": model_name,
        "vector_size": vector_size,
    }
