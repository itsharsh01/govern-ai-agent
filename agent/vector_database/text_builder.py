from __future__ import annotations

import json
from typing import Any

SKIP_KEYS = frozenset({"name", "category", "risk", "description"})

LABEL_DISPLAY = {
    "SensitiveFinancialData": "Sensitive Financial Data",
    "PersonalInformation": "Personal Information",
    "AgentTool": "Agent Tool",
    "AISecurityRisk": "AI Security Risk",
    "PrivacyRisk": "Privacy Risk",
    "ComplianceControl": "Compliance Control",
    "BankingRegulation": "Banking Regulation",
    "GovernanceRequirement": "Governance Requirement",
    "AIAgent": "AI Agent",
    "OntologyNode": "Ontology Node",
}


def primary_label(labels: list[str]) -> str:
    for label in labels:
        if label != "OntologyNode":
            return label
    return labels[0] if labels else "OntologyNode"


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def build_embedding_text(labels: list[str], props: dict[str, Any]) -> str:
    """Build rich text for embedding from Neo4j node labels and properties."""
    node_type = primary_label(labels)
    type_display = LABEL_DISPLAY.get(node_type, node_type.replace("_", " "))

    lines = [
        f"Node type: {type_display}",
        f"Name: {props.get('name', '(unnamed)')}",
    ]

    if props.get("category"):
        lines.append(f"Category: {props['category']}")
    if props.get("risk"):
        lines.append(f"Risk level: {props['risk']}")
    if props.get("description"):
        lines.append(f"Description: {props['description']}")

    extras: list[str] = []
    for key, value in sorted(props.items()):
        if key in SKIP_KEYS or value is None or value == "":
            continue
        formatted = _format_value(value)
        if formatted:
            label = key.replace("_", " ")
            extras.append(f"{label}: {formatted}")

    if extras:
        lines.append("Attributes: " + "; ".join(extras))

    return "\n".join(lines)
