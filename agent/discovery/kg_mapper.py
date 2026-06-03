from __future__ import annotations

from typing import Any


def map_entities_to_kg(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Stub KG mapper — returns placeholder mappings for discovered entities."""
    mappings: list[dict[str, Any]] = []

    tools = schema.get("tooling", {}).get("tools", [])
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("tool_name")
        if not name:
            continue
        mappings.append(
            {
                "discovered_entity": name,
                "entity_type": "tool",
                "kg_node_id": None,
                "match_score": 0.0,
                "status": "pending_qdrant_lookup",
            }
        )

    data_types = schema.get("data_assets", {}).get("data_types_processed", {}).get("value") or []
    for data_type in data_types:
        mappings.append(
            {
                "discovered_entity": data_type,
                "entity_type": "data_asset",
                "kg_node_id": None,
                "match_score": 0.0,
                "status": "pending_qdrant_lookup",
            }
        )

    return mappings
