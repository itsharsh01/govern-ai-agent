from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class KnowledgeGraphInitResponse(BaseModel):
    customer_id: str
    status: str
    created_at: str | None = None


class KnowledgeGraphMapRequest(BaseModel):
    source: Literal["discovery", "customer"]
    session_id: str | None = None
    replace_existing: bool = False


class EntityMappingResponse(BaseModel):
    source_key: str
    source_value: str
    instance_id: str
    ontology_node_id: str
    ontology_name: str
    ontology_node_type: str
    match_score: float
    match_method: str
    status: str
    entity_type: str


class KnowledgeGraphMapResponse(BaseModel):
    mapping_run_id: str
    customer_id: str
    mapped_count: int
    skipped_count: int
    low_confidence: list[dict[str, Any]] = Field(default_factory=list)
    neo4j_stats: dict[str, int] = Field(default_factory=dict)
    entities: list[EntityMappingResponse] = Field(default_factory=list)


class KnowledgeGraphSummaryResponse(BaseModel):
    customer_id: str
    graph: dict[str, Any] = Field(default_factory=dict)
    instances: list[dict[str, Any]] = Field(default_factory=list)
    last_mapping_run: dict[str, Any] | None = None
