from __future__ import annotations

from typing import Any

from agent.discovery_v2.models import CompletionOutputs, SessionState


def generate_completion(state: SessionState) -> CompletionOutputs:
    d = state.discovered
    purpose = d.get("system_profile.business_purpose")
    description = d.get("system_profile.system_description")
    industry = d.get("system_profile.industry")
    use_case = d.get("system_profile.primary_use_case")
    framework = d.get("architecture.framework")

    parts = ["Jupiter Discovery has completed your governance profile."]
    if purpose:
        parts.append(f"Business purpose: {purpose.value}.")
    if description and (not purpose or description.value != purpose.value):
        parts.append(f"Description: {description.value}.")
    if industry:
        parts.append(f"Industry: {industry.value}.")
    if use_case:
        parts.append(f"Use case: {use_case.value}.")
    if framework:
        parts.append(f"Framework: {framework.value}.")

    flag_messages = {
        "payment_api": "Payment-related APIs — verify human approval workflows.",
        "pii_to_llm": "PII may be sent to external LLM providers.",
        "autonomous_actions": "High autonomy on sensitive operations.",
        "missing_audit_logging": "Audit logging not confirmed.",
        "kyc_data_exposure": "KYC/CRM may expose identity data.",
        "write_operations": "Write operations — validate authorization.",
    }
    risks: list[dict[str, Any]] = []
    for flag in state.high_risk_flags_triggered:
        risks.append(
            {
                "flag": flag,
                "message": flag_messages.get(flag, f"Risk flag: {flag}"),
                "severity": "high",
            }
        )

    readiness = {
        "completion_pct": state.completion_pct,
        "fields_discovered": len(state.discovered),
        "flags_triggered": state.high_risk_flags_triggered,
        "confidence_met": state.completion_criteria.confidence_met,
        "all_required_filled": state.completion_criteria.all_required_filled,
    }

    return CompletionOutputs(
        system_summary=" ".join(parts),
        discovered=state.discovered,
        discovered_risks=risks,
        governance_readiness_report=readiness,
    )
