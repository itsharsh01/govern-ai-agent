from __future__ import annotations

from typing import Any

from agent.discovery.kg_mapper import map_entities_to_kg
from agent.discovery.models import DigitalTwinOutput
from agent.discovery.schema_utils import field_is_empty, walk_schema_fields

AUDIT_CRITICAL_PATHS = (
    "security.audit_logging_enabled",
    "security.output_filtering",
    "security.authentication_method",
    "security.authorization_model",
    "data_assets.pii_sent_to_external_llm",
    "data_assets.data_encryption.at_rest",
    "data_assets.data_encryption.in_transit",
    "tooling.human_approval_config.human_approval_required",
    "compliance.consent_management",
    "compliance.model_governance_framework",
    "policies.internal_ai_policy",
    "risk_profile.incident_response_process",
)


class DigitalTwinGenerator:
    def generate(self, schema: dict[str, Any]) -> DigitalTwinOutput:
        summary = self._build_summary(schema)
        risks = self._discover_risks(schema)
        readiness = self._readiness_report(schema)
        mappings = map_entities_to_kg(schema)
        return DigitalTwinOutput(
            system_summary=summary,
            digital_twin=schema,
            discovered_risks=risks,
            governance_readiness_report=readiness,
            kg_mappings=mappings,
        )

    def _build_summary(self, schema: dict[str, Any]) -> str:
        purpose = schema["system_profile"]["business_purpose"].get("value")
        description = schema["system_profile"]["system_description"].get("value")
        industry = schema["system_profile"]["industry"].get("value")
        use_case = schema["system_profile"]["primary_use_case"].get("value")
        framework = schema["architecture"]["framework"].get("value")
        tools = [
            t.get("tool_name")
            for t in schema.get("tooling", {}).get("tools", [])
            if isinstance(t, dict) and t.get("tool_name")
        ]

        parts = ["Jupiter Discovery has built a Digital Twin of your AI system."]
        if purpose:
            parts.append(f"Business purpose: {purpose}.")
        if description and description != purpose:
            parts.append(f"System description: {description}.")
        if industry:
            parts.append(f"Industry: {industry}.")
        if use_case:
            parts.append(f"Primary use case: {use_case}.")
        if framework:
            parts.append(f"Framework: {framework}.")
        if tools:
            parts.append(f"Integrated tools/APIs: {', '.join(str(t) for t in tools)}.")
        return " ".join(parts)

    def _discover_risks(self, schema: dict[str, Any]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        flags = schema["discovery_state"].get("high_risk_flags_triggered") or []

        flag_messages = {
            "payment_api": "Payment-related APIs detected — verify human approval workflows.",
            "pii_to_llm": "Customer PII may be sent to external LLM providers.",
            "autonomous_actions": "Agent may operate with high autonomy on sensitive operations.",
            "missing_audit_logging": "Sensitive integrations detected but audit logging not confirmed.",
            "kyc_data_exposure": "KYC or CRM integrations may expose customer identity data.",
            "write_operations": "Write or approval actions detected — validate authorization controls.",
        }
        for flag in flags:
            risks.append(
                {
                    "risk_id": flag,
                    "severity": "high",
                    "description": flag_messages.get(flag, flag),
                    "source": "discovery_state.high_risk_flags_triggered",
                }
            )

        pii_to_llm = schema["data_assets"]["pii_sent_to_external_llm"]
        if pii_to_llm.get("value") is True:
            risks.append(
                {
                    "risk_id": "privacy_pii_external_llm",
                    "severity": "critical",
                    "description": "PII is sent to external LLM providers.",
                    "source": "data_assets.pii_sent_to_external_llm",
                }
            )

        for path, field in walk_schema_fields(schema.get("risk_profile", {}), "risk_profile"):
            if path.endswith("identified_risks") and not field_is_empty(field):
                for item in field.get("value") or []:
                    risks.append(
                        {
                            "risk_id": "customer_identified",
                            "severity": "medium",
                            "description": str(item),
                            "source": path,
                        }
                    )
        return risks

    def _readiness_report(self, schema: dict[str, Any]) -> dict[str, Any]:
        checklist = []
        for path in AUDIT_CRITICAL_PATHS:
            try:
                from agent.discovery.schema_utils import get_at_path

                field = get_at_path(schema, path)
            except KeyError:
                continue
            if not isinstance(field, dict):
                continue
            checklist.append(
                {
                    "field_path": path,
                    "filled": not field_is_empty(field),
                    "confidence": field.get("confidence", 0),
                }
            )

        filled = sum(1 for item in checklist if item["filled"])
        return {
            "audit_critical_controls": checklist,
            "controls_filled": filled,
            "controls_total": len(checklist),
            "readiness_score": round(filled / len(checklist), 4) if checklist else 0.0,
            "overall_completeness": schema["discovery_state"]["overall_completeness"],
            "overall_confidence": schema["discovery_state"]["overall_confidence"],
        }
