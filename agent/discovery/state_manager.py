from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.discovery.models import ExtractedFact, GapKind
from agent.discovery.schema_utils import (
    PROFILE_SECTIONS,
    field_is_empty,
    get_at_path,
    is_schema_field,
    walk_schema_fields,
)

CONFIDENCE_WRITE_THRESHOLD = 0.6
HIGH_CONFIDENCE = 0.8
LOW_CONFIDENCE = 0.7


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _merge_list_values(existing: list[Any], incoming: Any) -> list[Any]:
    merged = list(existing or [])
    items = incoming if isinstance(incoming, list) else [incoming]
    for item in items:
        if item not in merged:
            merged.append(item)
    return merged


def _normalize_tool_entry(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "tool_name": value.get("tool_name") or value.get("name") or str(value),
            "tool_description": value.get("tool_description") or value.get("description"),
            "access_required": value.get("access_required"),
            "access_currently_has": value.get("access_currently_has"),
            "human_approval_required": value.get("human_approval_required"),
            "approval_for": value.get("approval_for") or [],
        }
    return {
        "tool_name": str(value),
        "tool_description": None,
        "access_required": None,
        "access_currently_has": None,
        "human_approval_required": None,
        "approval_for": [],
    }


class DiscoveryStateManager:
    def apply_facts(
        self,
        schema: dict[str, Any],
        facts: list[ExtractedFact],
        source_message: str,
    ) -> list[ExtractedFact]:
        applied: list[ExtractedFact] = []
        state = schema["discovery_state"]

        for fact in facts:
            if fact.confidence < CONFIDENCE_WRITE_THRESHOLD:
                state["inferred_facts"].append(
                    {
                        "type": fact.type,
                        "field_path": fact.field_path,
                        "value": fact.value,
                        "confidence": fact.confidence,
                        "requires_validation": True,
                        "source": source_message,
                    }
                )
                state["information_sources"]["inferred_from_context"].append(
                    {"field_path": fact.field_path, "value": fact.value, "confidence": fact.confidence}
                )
                continue

            if not fact.field_path:
                continue

            try:
                target = get_at_path(schema, fact.field_path)
            except KeyError:
                continue

            if fact.field_path == "tooling.tools":
                tools = schema["tooling"]["tools"]
                if tools and tools[0].get("tool_name") is None:
                    tools.pop(0)
                tools.append(_normalize_tool_entry(fact.value))
                applied.append(fact)
                self._record_fact(state, fact, source_message)
                continue

            if not is_schema_field(target):
                continue

            existing_value = target.get("value")
            if not field_is_empty(target) and existing_value != fact.value:
                if target.get("confidence", 0) >= HIGH_CONFIDENCE:
                    state["information_sources"]["contradictions_detected"].append(
                        {
                            "field_path": fact.field_path,
                            "existing_value": existing_value,
                            "new_value": fact.value,
                            "new_confidence": fact.confidence,
                        }
                    )
                    target["confidence"] = max(0.3, target.get("confidence", 0) - 0.2)
                    continue

            if isinstance(target.get("value"), list):
                target["value"] = _merge_list_values(target.get("value") or [], fact.value)
            else:
                target["value"] = fact.value
            target["confidence"] = fact.confidence
            target["source"] = source_message
            applied.append(fact)
            self._record_fact(state, fact, source_message)

        state["facts_extracted_total"] += len(applied)
        self.recompute_scores(schema)
        self._update_high_risk_flags(schema)
        return applied

    def _record_fact(self, state: dict[str, Any], fact: ExtractedFact, source_message: str) -> None:
        entry = {
            "type": fact.type,
            "field_path": fact.field_path,
            "value": fact.value,
            "confidence": fact.confidence,
            "source": source_message,
        }
        state["known_facts"].append(entry)
        state["information_sources"]["customer_stated"].append(entry)

    def recompute_scores(self, schema: dict[str, Any]) -> None:
        state = schema["discovery_state"]
        section_scores: dict[str, tuple[float, float]] = {}

        for section in PROFILE_SECTIONS:
            completeness, confidence = self._score_section(schema, section)
            section_scores[section] = (completeness, confidence)
            progress = state["section_progress"][section]
            progress["completeness"] = round(completeness, 4)
            progress["confidence"] = round(confidence, 4)
            if completeness >= 0.95:
                progress["status"] = "complete"
            elif completeness > 0:
                progress["status"] = "in_progress"
            else:
                progress["status"] = "not_started"

        if section_scores:
            state["overall_completeness"] = round(
                sum(v[0] for v in section_scores.values()) / len(section_scores),
                4,
            )
            conf_values = [v[1] for v in section_scores.values() if v[1] > 0]
            state["overall_confidence"] = round(
                sum(conf_values) / len(conf_values) if conf_values else 0.0,
                4,
            )
        else:
            state["overall_completeness"] = 0.0
            state["overall_confidence"] = 0.0

        state["discovery_phase"]["value"] = self._phase_for_completeness(state["overall_completeness"])
        state["last_updated_at"] = _now_iso()

    def _score_section(self, schema: dict[str, Any], section: str) -> tuple[float, float]:
        required_fields: list[dict[str, Any]] = []
        for path, field in walk_schema_fields(schema.get(section, {}), section):
            if field.get("required") is True:
                required_fields.append(field)

        if not required_fields:
            optional_fields = [f for _, f in walk_schema_fields(schema.get(section, {}), section)]
            if not optional_fields:
                return 1.0, 1.0
            filled = sum(1 for f in optional_fields if not field_is_empty(f))
            avg_conf = sum(f.get("confidence", 0) for f in optional_fields if not field_is_empty(f))
            count_filled = sum(1 for f in optional_fields if not field_is_empty(f))
            return filled / len(optional_fields), (avg_conf / count_filled if count_filled else 0.0)

        filled_weight = 0.0
        confidence_sum = 0.0
        confidence_count = 0
        for field in required_fields:
            if not field_is_empty(field):
                filled_weight += field.get("confidence", 0.5)
                confidence_sum += field.get("confidence", 0)
                confidence_count += 1

        completeness = filled_weight / len(required_fields)
        confidence = confidence_sum / confidence_count if confidence_count else 0.0
        return completeness, confidence

    def _phase_for_completeness(self, completeness: float) -> str:
        if completeness >= 0.95:
            return "complete"
        if completeness >= 0.75:
            return "validation"
        if completeness >= 0.55:
            return "gap_filling"
        if completeness >= 0.35:
            return "deep_dive"
        if completeness >= 0.1:
            return "core_discovery"
        return "initial"

    def _update_high_risk_flags(self, schema: dict[str, Any]) -> None:
        flags: set[str] = set()
        tools = schema.get("tooling", {}).get("tools", [])
        tool_names = " ".join(
            str(t.get("tool_name", "")).lower() for t in tools if isinstance(t, dict)
        )
        apis = schema.get("tooling", {}).get("apis", {}).get("api_list", {}).get("value") or []
        api_text = " ".join(str(a).lower() for a in apis)

        combined = f"{tool_names} {api_text}"
        from agent.discovery.templates import PAYMENT_KEYWORDS, PII_KEYWORDS, WRITE_KEYWORDS

        if any(kw in combined for kw in PAYMENT_KEYWORDS):
            flags.add("payment_api")
        if any(kw in combined for kw in PII_KEYWORDS):
            flags.add("kyc_data_exposure")
        if any(kw in combined for kw in WRITE_KEYWORDS):
            flags.add("write_operations")

        agentic = schema.get("architecture", {}).get("agentic", {}).get("is_agentic", {})
        if agentic.get("value") is True:
            autonomy = schema.get("architecture", {}).get("agentic", {}).get("autonomy_level", {})
            if autonomy.get("value") == "fully_autonomous":
                flags.add("autonomous_actions")

        pii_to_llm = schema.get("data_assets", {}).get("pii_sent_to_external_llm", {})
        if pii_to_llm.get("value") is True:
            flags.add("pii_to_llm")

        audit = schema.get("security", {}).get("audit_logging_enabled", {})
        if field_is_empty(audit) and ("kyc" in combined or "crm" in combined):
            flags.add("missing_audit_logging")

        schema["discovery_state"]["high_risk_flags_triggered"] = sorted(flags)

    def build_understanding_summary(self, schema: dict[str, Any]) -> list[str]:
        bullets: list[str] = []
        for fact in schema["discovery_state"]["known_facts"][-20:]:
            path = fact.get("field_path") or fact.get("type", "fact")
            value = fact.get("value")
            bullets.append(f"{path}: {value}")
        return bullets[:10]

    def check_completion(self, schema: dict[str, Any], critical_gaps: list[Any]) -> bool:
        state = schema["discovery_state"]
        criteria = state["completion_criteria"]
        unresolved = [g for g in critical_gaps if g.kind in {GapKind.MISSING, GapKind.LOW_CONFIDENCE}]

        criteria["confidence_threshold_met"] = state["overall_confidence"] >= criteria["minimum_confidence_required"]
        criteria["completeness_threshold_met"] = state["overall_completeness"] >= criteria[
            "minimum_completeness_required"
        ]
        criteria["all_critical_fields_filled"] = len(unresolved) == 0
        criteria["all_high_risk_flags_resolved"] = self._high_risk_flags_resolved(schema)

        complete = (
            criteria["confidence_threshold_met"]
            and criteria["completeness_threshold_met"]
            and criteria["all_critical_fields_filled"]
            and criteria["all_high_risk_flags_resolved"]
        )
        state["discovery_complete"] = complete
        if complete:
            state["discovery_phase"]["value"] = "complete"
        return complete

    def _high_risk_flags_resolved(self, schema: dict[str, Any]) -> bool:
        flags = set(schema["discovery_state"].get("high_risk_flags_triggered") or [])
        if "pii_to_llm" in flags:
            field = schema["data_assets"]["pii_sent_to_external_llm"]
            if field_is_empty(field):
                return False
        if "payment_api" in flags:
            approval = schema["tooling"]["human_approval_config"]["human_approval_required"]
            if field_is_empty(approval):
                return False
        if "missing_audit_logging" in flags:
            audit = schema["security"]["audit_logging_enabled"]
            if field_is_empty(audit):
                return False
        if "autonomous_actions" in flags:
            autonomy = schema["architecture"]["agentic"]["autonomy_level"]
            if field_is_empty(autonomy):
                return False
        return True

    def init_session_metadata(self, schema: dict[str, Any], session_id: str) -> None:
        state = schema["discovery_state"]
        now = _now_iso()
        state["session_id"] = session_id
        state["started_at"] = now
        state["last_updated_at"] = now
        state["conversation_turns"] = 0

    def increment_turn(self, schema: dict[str, Any]) -> None:
        schema["discovery_state"]["conversation_turns"] += 1
