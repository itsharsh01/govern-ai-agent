from __future__ import annotations

from typing import Any

from agent.discovery.models import InteractionOption, InteractionRequest, InteractionType
from agent.discovery.schema_utils import get_at_path, is_schema_field

MULTI_SELECT_FIELDS: dict[str, str] = {
    "data_assets.data_types_processed": "Data types your system processes",
    "data_assets.pii_categories": "PII categories the system can access",
    "compliance.applicable_regulations": "Regulations that apply to this system",
    "users_and_customers.user_types": "Who uses this system internally",
    "users_and_customers.customer_types": "Types of customers served",
    "users_and_customers.geographic_regions": "Geographic regions where the system operates",
    "tooling.human_approval_config.approval_for": "Actions requiring human approval",
    "system_profile.industry": "Industry segment",
    "system_profile.primary_use_case": "Primary use case",
    "architecture.system_type": "System architecture type",
    "architecture.framework": "Agent / LLM framework",
    "models.primary_llm.provider": "Primary LLM provider",
}

DOCUMENT_UPLOAD_FIELDS: dict[str, str] = {
    "policies.policy_document_refs": "Internal AI and governance policy documents",
    "knowledge_sources.document_uploads.internal_policy_documents": "Internal policy documents for RAG",
    "knowledge_sources.document_uploads.system_policy_documents": "System-level policy documents",
    "knowledge_sources.document_uploads.other_policy_documents": "Other compliance or policy documents",
}

MULTI_INPUT_FIELDS: dict[str, dict[str, str]] = {
    "tooling.apis.api_list": {
        "label": "EXTERNAL_APIS",
        "placeholder": "Add API name (e.g. CRM, KYC, Payment Gateway)",
        "key_label": "API",
    },
    "risk_profile.identified_risks": {
        "label": "IDENTIFIED_RISKS",
        "placeholder": "Describe a risk you are aware of",
        "key_label": "RISK",
    },
    "risk_profile.mitigations_in_place": {
        "label": "MITIGATIONS",
        "placeholder": "Describe a control or mitigation in place",
        "key_label": "CONTROL",
    },
}


def _format_option_label(value: str) -> str:
    return value.replace("_", " ").upper()


def _options_from_field(field: dict[str, Any]) -> list[InteractionOption]:
    allowed = field.get("allowed_values") or []
    return [
        InteractionOption(id=str(v), label=_format_option_label(str(v)), description="")
        for v in allowed
    ]


def resolve_interaction(schema: dict[str, Any], field_path: str, prompt: str) -> InteractionRequest | None:
    if field_path in DOCUMENT_UPLOAD_FIELDS:
        return InteractionRequest(
            type=InteractionType.DOCUMENT_UPLOAD,
            field_path=field_path,
            prompt=prompt,
            accept=".pdf,.json,.yaml,.yml",
            max_files=5,
        )

    if field_path in MULTI_INPUT_FIELDS:
        meta = MULTI_INPUT_FIELDS[field_path]
        return InteractionRequest(
            type=InteractionType.MULTI_INPUT,
            field_path=field_path,
            prompt=prompt,
            input_label=meta["label"],
            input_placeholder=meta["placeholder"],
            key_label=meta.get("key_label", "ITEM"),
        )

    if field_path in MULTI_SELECT_FIELDS:
        try:
            field = get_at_path(schema, field_path)
        except KeyError:
            field = {}
        options = _options_from_field(field) if isinstance(field, dict) else []
        if not options:
            return None
        return InteractionRequest(
            type=InteractionType.MULTI_SELECT,
            field_path=field_path,
            prompt=prompt,
            options=options,
            min_selections=1,
        )

    # Enum-like single-select fields
    try:
        field = get_at_path(schema, field_path)
    except KeyError:
        return None
    if is_schema_field(field) and field.get("allowed_values"):
        return InteractionRequest(
            type=InteractionType.MULTI_SELECT,
            field_path=field_path,
            prompt=prompt,
            options=_options_from_field(field),
            min_selections=1,
            max_selections=1,
        )

    return InteractionRequest(
        type=InteractionType.TEXT,
        field_path=field_path,
        prompt=prompt,
    )
