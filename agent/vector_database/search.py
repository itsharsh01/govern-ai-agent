from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from qdrant_client.http import models

DEFAULT_SCORE_THRESHOLD = 0.58


@dataclass(frozen=True)
class OntologySearchQuery:
    query_id: str
    text: str
    node_types: tuple[str, ...] = ()
    extra_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class OntologySearchHit:
    query_id: str
    neo4j_id: str
    name: str
    node_type: str
    score: float
    match_method: str = "semantic"


def normalize_name(value: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


@lru_cache(maxsize=1)
def _ontology_name_index() -> dict[str, dict[str, Any]]:
    from agent.vector_database.indexer import fetch_ontology_nodes

    index: dict[str, dict[str, Any]] = {}
    for node in fetch_ontology_nodes():
        key = normalize_name(node["name"])
        if key and key not in index:
            index[key] = node
    return index


def clear_ontology_name_cache() -> None:
    _ontology_name_index.cache_clear()


def exact_match(
    text: str,
    node_types: tuple[str, ...] = (),
    *,
    extra_terms: tuple[str, ...] = (),
) -> OntologySearchHit | None:
    from agent.knowledge_graph.ontology_aliases import ONTOLOGY_NAME_ALIASES

    index = _ontology_name_index()
    candidates: list[str] = []
    for raw in (text, *extra_terms):
        norm = normalize_name(raw)
        if not norm:
            continue
        candidates.append(ONTOLOGY_NAME_ALIASES.get(norm, norm))
        if norm in ONTOLOGY_NAME_ALIASES:
            candidates.append(norm)

    node = None
    for key in candidates:
        node = index.get(key)
        if node is not None:
            break
    if node is None:
        return None
    if node_types and node["node_type"] not in node_types:
        return None
    return OntologySearchHit(
        query_id="",
        neo4j_id=node["neo4j_id"],
        name=node["name"],
        node_type=node["node_type"],
        score=1.0,
        match_method="exact",
    )


def _build_filter(node_types: tuple[str, ...]) -> models.Filter | None:
    if not node_types:
        return None
    if len(node_types) == 1:
        match: models.MatchValue | models.MatchAny = models.MatchValue(value=node_types[0])
    else:
        match = models.MatchAny(any=list(node_types))
    return models.Filter(
        must=[
            models.FieldCondition(
                key="node_type",
                match=match,
            )
        ]
    )


def search_ontology_batch(
    queries: list[OntologySearchQuery],
    *,
    top_k: int = 1,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    qdrant_settings: Any | None = None,
) -> dict[str, OntologySearchHit | None]:
    from agent.vector_database.client import get_client
    from agent.vector_database.collection import ensure_payload_indexes
    from agent.vector_database.config import QdrantSettings
    from agent.vector_database.embedder import embed_texts

    if not queries:
        return {}

    qdrant_settings = qdrant_settings or QdrantSettings.from_env()
    results: dict[str, OntologySearchHit | None] = {}
    semantic_queries: list[OntologySearchQuery] = []

    for query in queries:
        exact = exact_match(
            query.text,
            query.node_types,
            extra_terms=query.extra_terms,
        )
        if exact is not None:
            results[query.query_id] = OntologySearchHit(
                query_id=query.query_id,
                neo4j_id=exact.neo4j_id,
                name=exact.name,
                node_type=exact.node_type,
                score=exact.score,
                match_method="exact",
            )
        else:
            semantic_queries.append(query)

    if not semantic_queries:
        return results

    vectors = embed_texts(
        [query.text for query in semantic_queries],
        model_name=qdrant_settings.embedding_model,
    )
    client = get_client()
    ensure_payload_indexes(client, qdrant_settings.collection_name)
    requests = [
        models.QueryRequest(
            query=vector,
            filter=_build_filter(query.node_types),
            limit=top_k,
            with_payload=True,
        )
        for query, vector in zip(semantic_queries, vectors, strict=True)
    ]
    batch = client.query_batch_points(
        collection_name=qdrant_settings.collection_name,
        requests=requests,
    )

    for query, response in zip(semantic_queries, batch, strict=True):
        points = response.points or []
        if not points:
            results[query.query_id] = None
            continue
        hit = points[0]
        payload = hit.payload or {}
        results[query.query_id] = OntologySearchHit(
            query_id=query.query_id,
            neo4j_id=str(payload.get("neo4j_id", "")),
            name=str(payload.get("name", "")),
            node_type=str(payload.get("node_type", "")),
            score=float(hit.score or 0.0),
            match_method="semantic",
        )

    return results
