from __future__ import annotations

from typing import Any

from agent.discovery.models import GapKind, RankedGap, SchemaGap
from agent.discovery.templates import (
    FIELD_BOOST,
    INFORMATION_GAIN_FIELDS,
    SECTION_CATEGORY_WEIGHT,
)


class RiskPrioritizationEngine:
    PRIORITY_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.3}

    def prioritize(self, schema: dict[str, Any], gaps: list[SchemaGap]) -> list[RankedGap]:
        flags = set(schema["discovery_state"].get("high_risk_flags_triggered") or [])
        ranked: list[RankedGap] = []

        for gap in gaps:
            score = self._base_score(gap)
            score += FIELD_BOOST.get(gap.field_path, 0) * 0.5
            score += self._flag_boost(gap, flags)
            if gap.field_path in INFORMATION_GAIN_FIELDS:
                score += 0.25
            if gap.kind == GapKind.INFERRED_UNVALIDATED:
                score += 0.15
            if gap.kind == GapKind.MISSING and gap.required:
                score += 0.2

            ranked.append(
                RankedGap(
                    field_path=gap.field_path,
                    section=gap.section,
                    risk_score=round(score, 4),
                    kind=gap.kind,
                    rationale=gap.rationale,
                )
            )

        ranked.sort(key=lambda item: item.risk_score, reverse=True)
        schema["discovery_state"]["critical_gaps"] = [
            {
                "field_path": g.field_path,
                "section": g.section,
                "risk_score": g.risk_score,
                "kind": g.kind.value,
                "rationale": g.rationale,
            }
            for g in ranked[:10]
        ]
        return ranked

    def _base_score(self, gap: SchemaGap) -> float:
        section_weight = SECTION_CATEGORY_WEIGHT.get(gap.section, 0.3)
        priority_weight = self.PRIORITY_WEIGHT.get(gap.priority, 0.5)
        kind_weight = {
            GapKind.MISSING: 1.0,
            GapKind.INFERRED_UNVALIDATED: 0.85,
            GapKind.LOW_CONFIDENCE: 0.7,
        }[gap.kind]
        return section_weight * priority_weight * kind_weight

    def _flag_boost(self, gap: SchemaGap, flags: set[str]) -> float:
        boost = 0.0
        if "payment_api" in flags and gap.field_path.startswith("tooling"):
            boost += 0.3
        if "kyc_data_exposure" in flags and gap.section == "data_assets":
            boost += 0.35
        if "pii_to_llm" in flags and gap.field_path == "data_assets.pii_sent_to_external_llm":
            boost += 0.4
        if "missing_audit_logging" in flags and gap.field_path == "security.audit_logging_enabled":
            boost += 0.35
        if "autonomous_actions" in flags and gap.field_path.startswith("architecture.agentic"):
            boost += 0.3
        if "write_operations" in flags and gap.field_path.startswith("tooling.human_approval"):
            boost += 0.3
        return boost
