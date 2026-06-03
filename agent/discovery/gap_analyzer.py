from __future__ import annotations

from typing import Any

from agent.discovery.models import GapKind, SchemaGap
from agent.discovery.schema_utils import field_is_empty, get_field_value, walk_schema_fields


def _is_truthy(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() in {"true", "yes"})


def _should_skip_field(schema: dict[str, Any], path: str) -> bool:
    try:
        is_agentic = get_field_value(schema, "architecture.agentic.is_agentic")
    except KeyError:
        is_agentic = None
    try:
        uses_rag = get_field_value(schema, "knowledge_sources.uses_rag")
    except KeyError:
        uses_rag = None
    try:
        is_multi_agent = get_field_value(schema, "architecture.multi_agent.is_multi_agent")
    except KeyError:
        is_multi_agent = None

    if not _is_truthy(is_agentic):
        agentic_only = {
            "architecture.data_flow.tool_execution_flow",
            "architecture.agentic.autonomy_level",
            "architecture.agentic.orchestration_pattern",
        }
        if path in agentic_only:
            return True

    if not _is_truthy(uses_rag):
        rag_only = {
            "architecture.data_flow.retrieval_flow",
            "knowledge_sources.knowledge_base_description",
        }
        if path in rag_only:
            return True

    if not _is_truthy(is_multi_agent):
        multi_only = {
            "architecture.multi_agent.number_of_agents",
            "architecture.multi_agent.agent_communication_protocol",
        }
        if path in multi_only:
            return True

    return False


class GapAnalysisEngine:
    def analyze(self, schema: dict[str, Any]) -> list[SchemaGap]:
        gaps: list[SchemaGap] = []
        inferred_paths = {
            item.get("field_path")
            for item in schema["discovery_state"].get("inferred_facts", [])
            if item.get("field_path")
        }

        for path, field in walk_schema_fields(schema):
            if path.startswith("discovery_state"):
                continue
            if _should_skip_field(schema, path):
                continue

            required = field.get("required") is True
            if not required and field_is_empty(field):
                continue

            if field_is_empty(field):
                gaps.append(
                    SchemaGap(
                        field_path=path,
                        section=path.split(".", 1)[0],
                        kind=GapKind.MISSING,
                        required=required,
                        priority=field.get("priority", "medium"),
                        current_confidence=field.get("confidence", 0),
                        rationale="Required field has no value" if required else "Optional field empty",
                    )
                )
                continue

            if path in inferred_paths:
                gaps.append(
                    SchemaGap(
                        field_path=path,
                        section=path.split(".", 1)[0],
                        kind=GapKind.INFERRED_UNVALIDATED,
                        required=required,
                        priority=field.get("priority", "medium"),
                        current_confidence=field.get("confidence", 0),
                        rationale="Inferred value requires customer validation",
                    )
                )
                continue

            if field.get("confidence", 0) < 0.7:
                gaps.append(
                    SchemaGap(
                        field_path=path,
                        section=path.split(".", 1)[0],
                        kind=GapKind.LOW_CONFIDENCE,
                        required=required,
                        priority=field.get("priority", "medium"),
                        current_confidence=field.get("confidence", 0),
                        rationale="Field value confidence below threshold",
                    )
                )

        state = schema["discovery_state"]
        state["unknown_areas"] = [
            {"field_path": g.field_path, "kind": g.kind.value, "rationale": g.rationale}
            for g in gaps
            if g.kind == GapKind.MISSING
        ]
        return gaps
