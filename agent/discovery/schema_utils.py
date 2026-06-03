from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Iterator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "jupiter_discovery_schema_v2.json"

PROFILE_SECTIONS = (
    "system_profile",
    "users_and_customers",
    "architecture",
    "models",
    "tooling",
    "data_assets",
    "knowledge_sources",
    "system_access",
    "policies",
    "security",
    "compliance",
    "risk_profile",
)


def load_schema_template() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def new_session_schema(session_id: str) -> dict[str, Any]:
    schema = copy.deepcopy(load_schema_template())
    state = schema["discovery_state"]
    state["session_id"] = session_id
    return schema


def is_schema_field(node: Any) -> bool:
    return isinstance(node, dict) and "value" in node and "confidence" in node


def walk_schema_fields(
    node: Any,
    prefix: str = "",
    *,
    section_filter: str | None = None,
) -> Iterator[tuple[str, dict[str, Any]]]:
    if is_schema_field(node):
        if section_filter is None or prefix.startswith(section_filter):
            yield prefix, node
        return

    if not isinstance(node, dict):
        return

    for key, child in node.items():
        if key == "discovery_state":
            continue
        child_prefix = f"{prefix}.{key}" if prefix else key
        if section_filter and not child_prefix.startswith(section_filter):
            if not any(child_prefix.startswith(s) for s in PROFILE_SECTIONS):
                continue
        yield from walk_schema_fields(child, child_prefix, section_filter=section_filter)


def get_at_path(schema: dict[str, Any], path: str) -> Any:
    current: Any = schema
    for part in path.split("."):
        if isinstance(current, list):
            raise KeyError(f"Cannot traverse list at {path}")
        current = current[part]
    return current


def set_at_path(schema: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = schema
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


def get_field_value(schema: dict[str, Any], path: str) -> Any:
    field = get_at_path(schema, path)
    if not is_schema_field(field):
        raise ValueError(f"{path} is not a schema field")
    return field.get("value")


def field_is_empty(field: dict[str, Any]) -> bool:
    value = field.get("value")
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, str):
        return value.strip() == ""
    return False


def section_for_path(path: str) -> str:
    return path.split(".", 1)[0]
