from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from agent.knowledge_graph.customer_graph import (
    delete_customer_instances,
    init_customer_graph,
    propagate_can_access,
    write_instance_mappings,
)
from agent.knowledge_graph.entity_extractor import (
    MappableEntity,
    extract_from_customer,
    extract_from_discovery,
)
from agent.knowledge_graph.models import EntityMappingRecord
from agent.vector_database.search import (
    DEFAULT_SCORE_THRESHOLD,
    OntologySearchQuery,
    search_ontology_batch,
)

SourceType = Literal["discovery", "customer"]


@dataclass
class MappingRunResult:
    mapping_run_id: str
    customer_id: str
    source: dict[str, Any]
    entities: list[EntityMappingRecord]
    mapped_count: int
    skipped_count: int
    low_confidence: list[dict[str, Any]]
    neo4j_stats: dict[str, int]
    created_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _match_entities(
    entities: list[MappableEntity],
    *,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> tuple[list[EntityMappingRecord], list[dict[str, Any]], int]:
    if not entities:
        return [], [], 0

    queries = [
        OntologySearchQuery(
            query_id=entity.entity_id,
            text=entity.search_text,
            node_types=entity.node_types,
            extra_terms=(entity.display_name,),
        )
        for entity in entities
    ]
    hits = search_ontology_batch(queries, score_threshold=score_threshold)

    mapped: list[EntityMappingRecord] = []
    low_confidence: list[dict[str, Any]] = []
    skipped = 0

    for entity in entities:
        hit = hits.get(entity.entity_id)
        if hit is None or not hit.neo4j_id or hit.score < score_threshold:
            skipped += 1
            if hit is not None and hit.neo4j_id:
                low_confidence.append(
                    {
                        "source_key": entity.source_key,
                        "display_name": entity.display_name,
                        "best_match": hit.name,
                        "score": hit.score,
                    }
                )
            continue

        instance_id = str(uuid4())
        mapped.append(
            EntityMappingRecord(
                source_key=entity.source_key,
                source_value=entity.display_name,
                instance_id=instance_id,
                ontology_node_id=hit.neo4j_id,
                ontology_name=hit.name,
                ontology_node_type=hit.node_type,
                match_score=hit.score,
                match_method=hit.match_method,
                status="mapped",
                entity_type=entity.entity_type,
            )
        )

    return mapped, low_confidence, skipped


def run_mapping(
    customer_id: str,
    *,
    source_type: SourceType,
    session_id: str | None = None,
    discovered: dict[str, Any] | None = None,
    customer_record: Any | None = None,
    replace_existing: bool = False,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> MappingRunResult:
    init_customer_graph(customer_id)
    if replace_existing:
        delete_customer_instances(customer_id)

    if source_type == "discovery":
        if discovered is None:
            raise ValueError("discovered payload is required for discovery source")
        entities = extract_from_discovery(discovered)
        source = {"type": "discovery", "session_id": session_id}
    else:
        if customer_record is None:
            raise ValueError("customer_record is required for customer source")
        entities = extract_from_customer(customer_record)
        source = {"type": "customer"}

    mapped_records, low_confidence, skipped = _match_entities(
        entities,
        score_threshold=score_threshold,
    )
    neo4j_stats = write_instance_mappings(customer_id, mapped_records)
    propagated = propagate_can_access(customer_id)
    neo4j_stats["can_access_edges"] = propagated

    return MappingRunResult(
        mapping_run_id=str(uuid4()),
        customer_id=customer_id,
        source=source,
        entities=mapped_records,
        mapped_count=len(mapped_records),
        skipped_count=skipped,
        low_confidence=low_confidence,
        neo4j_stats=neo4j_stats,
        created_at=_now_iso(),
    )
