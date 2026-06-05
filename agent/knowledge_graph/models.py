from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityMappingRecord:
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
