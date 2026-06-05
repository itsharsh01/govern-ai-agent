from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from agent.discovery_v2.models import RiskQueueItem, RiskLevel

RISK_WEIGHTS: dict[RiskLevel, int] = {
    "CRITICAL": 40,
    "HIGH": 25,
    "MEDIUM": 10,
    "LOW": 0,
}

SECTION_WEIGHTS: dict[str, int] = {
    "security": 13,
    "data_assets": 12,
    "architecture": 12,
    "compliance": 11,
    "system_profile": 15,
    "models": 10,
    "tooling": 10,
    "risk_profile": 10,
    "knowledge_sources": 8,
    "users_and_customers": 9,
    "policies": 17,
    "system_access": 5,
    "operational": 5,
}

INTERNAL_FLAG_PREFIX = "_flag."

# Keys that are flags, not schema fields — handled via high_risk_flags_triggered
INTERNAL_UNLOCK_FLAGS = frozenset({"_flag.missing_audit_logging"})

PRIORITY_QUEUE_TEMPLATE: list[dict[str, Any]] = [
    {
        "key": "data_assets.pii_sent_to_external_llm",
        "priority_score": 62,
        "risk_level": "CRITICAL",
        "required": True,
        "answer_type": "boolean",
        "section": "data_assets",
        "label": "PII sent to external LLM API",
        "unlocks_on": {"true": ["data_assets.pii_categories"]},
    },
    {
        "key": "tooling.human_approval_config.human_approval_required",
        "priority_score": 62,
        "risk_level": "CRITICAL",
        "required": True,
        "answer_type": "boolean",
        "section": "tooling",
        "label": "Human approval required for tool calls",
        "unlocks_on": {"true": ["tooling.human_approval_config.approval_for"]},
    },
    {
        "key": "architecture.agentic.is_agentic",
        "priority_score": 57,
        "risk_level": "CRITICAL",
        "required": True,
        "answer_type": "boolean",
        "section": "architecture",
        "label": "Is the system agentic",
        "unlocks_on": {
            "true": [
                "architecture.agentic.autonomy_level",
                "architecture.agentic.orchestration_pattern",
            ]
        },
    },
    {
        "key": "security.authentication_method",
        "priority_score": 58,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "security",
        "label": "Authentication method",
        "allowed_values": ["oauth2", "saml", "api_key", "jwt", "mfa", "sso", "none", "mixed"],
    },
    {
        "key": "security.audit_logging_enabled",
        "priority_score": 58,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "boolean",
        "section": "security",
        "label": "Audit logging enabled",
        "unlocks_on": {"false": ["_flag.missing_audit_logging"]},
    },
    {
        "key": "data_assets.sensitive_financial_data",
        "priority_score": 55,
        "risk_level": "CRITICAL",
        "required": True,
        "answer_type": "free_text",
        "section": "data_assets",
        "label": "Sensitive financial data handled",
        "unlocks_on": None,
    },
    {
        "key": "compliance.applicable_regulations",
        "priority_score": 56,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "multi_enum",
        "section": "compliance",
        "label": "Applicable regulations",
        "allowed_values": [
            "gdpr",
            "ccpa",
            "pci_dss",
            "sox",
            "hipaa",
            "dora",
            "eu_ai_act",
            "rbi_guidelines",
            "sebi_regulations",
            "aml_cft",
            "other",
        ],
    },
    {
        "key": "system_profile.business_purpose",
        "priority_score": 50,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "system_profile",
        "label": "Business purpose of the system",
        "unlocks_on": None,
    },
    {
        "key": "system_profile.primary_use_case",
        "priority_score": 48,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "system_profile",
        "label": "Primary use case",
        "allowed_values": [
            "banking_assistant",
            "customer_support_agent",
            "kyc_assistant",
            "loan_assistant",
            "investment_advisor",
            "financial_analysis_agent",
            "agentic_rag",
            "multi_agent_system",
            "fraud_detection",
            "risk_scoring",
            "document_processing",
            "other",
        ],
    },
    {
        "key": "system_profile.industry",
        "priority_score": 46,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "system_profile",
        "label": "Industry vertical",
        "allowed_values": [
            "banking",
            "insurance",
            "investment",
            "payments",
            "lending",
            "wealth_management",
            "regtech",
            "fintech_other",
        ],
    },
    {
        "key": "system_profile.system_description",
        "priority_score": 44,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "system_profile",
        "label": "System description",
        "unlocks_on": None,
    },
    {
        "key": "models.primary_llm.provider",
        "priority_score": 45,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "models",
        "label": "LLM provider",
        "allowed_values": [
            "openai",
            "anthropic",
            "google",
            "meta",
            "mistral",
            "cohere",
            "azure_openai",
            "aws_bedrock",
            "huggingface",
            "custom_fine_tuned",
            "open_source_self_hosted",
            "other",
        ],
    },
    {
        "key": "models.primary_llm.model_name",
        "priority_score": 43,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "models",
        "label": "LLM model name",
        "unlocks_on": None,
    },
    {
        "key": "models.primary_llm.access_method",
        "priority_score": 42,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "models",
        "label": "Model access method",
        "allowed_values": ["api", "self_hosted", "fine_tuned_api", "bedrock", "azure_openai", "vertex_ai"],
    },
    {
        "key": "architecture.system_type",
        "priority_score": 47,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "architecture",
        "label": "System architecture type",
        "allowed_values": [
            "single_agent",
            "multi_agent",
            "rag_pipeline",
            "agentic_rag",
            "workflow_automation",
            "chatbot_only",
            "hybrid",
        ],
    },
    {
        "key": "architecture.framework",
        "priority_score": 40,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "architecture",
        "label": "AI framework used",
        "allowed_values": [
            "langchain",
            "langgraph",
            "llamaindex",
            "autogen",
            "crewai",
            "semantic_kernel",
            "haystack",
            "custom",
            "none",
            "other",
        ],
    },
    {
        "key": "architecture.data_flow.user_input_flow",
        "priority_score": 38,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "architecture",
        "label": "How user input flows through the system",
        "unlocks_on": None,
    },
    {
        "key": "architecture.data_flow.response_generation_flow",
        "priority_score": 36,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "architecture",
        "label": "How responses are generated",
        "unlocks_on": None,
    },
    {
        "key": "data_assets.data_types_processed",
        "priority_score": 47,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "multi_enum",
        "section": "data_assets",
        "label": "Data types processed",
        "allowed_values": [
            "customer_pii",
            "financial_data",
            "transaction_history",
            "credit_data",
            "kyc_documents",
            "aml_data",
            "account_data",
            "investment_portfolio",
            "behavioral_data",
            "biometric_data",
            "health_data",
            "employment_data",
            "internal_documents",
            "market_data",
            "regulatory_filings",
            "audit_logs",
            "communication_data",
            "geolocation_data",
            "device_data",
        ],
    },
    {
        "key": "data_assets.data_encryption.at_rest",
        "priority_score": 40,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "boolean",
        "section": "data_assets",
        "label": "Data encrypted at rest",
        "unlocks_on": None,
    },
    {
        "key": "data_assets.data_encryption.in_transit",
        "priority_score": 40,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "boolean",
        "section": "data_assets",
        "label": "Data encrypted in transit",
        "unlocks_on": None,
    },
    {
        "key": "security.authorization_model",
        "priority_score": 43,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "security",
        "label": "Authorization model",
        "allowed_values": ["rbac", "abac", "pbac", "none", "custom"],
    },
    {
        "key": "security.output_filtering",
        "priority_score": 43,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "boolean",
        "section": "security",
        "label": "Output filtering / guardrails",
        "unlocks_on": None,
    },
    {
        "key": "compliance.model_governance_framework",
        "priority_score": 43,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "compliance",
        "label": "Model governance framework",
        "unlocks_on": None,
    },
    {
        "key": "compliance.consent_management",
        "priority_score": 43,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "compliance",
        "label": "Consent management process",
        "unlocks_on": None,
    },
    {
        "key": "knowledge_sources.uses_rag",
        "priority_score": 38,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "boolean",
        "section": "knowledge_sources",
        "label": "Uses RAG",
        "unlocks_on": {
            "true": [
                "knowledge_sources.knowledge_base_description",
                "knowledge_sources.document_uploads",
            ]
        },
    },
    {
        "key": "users_and_customers.description",
        "priority_score": 35,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "users_and_customers",
        "label": "Who uses the system",
        "unlocks_on": None,
    },
    {
        "key": "users_and_customers.geographic_regions",
        "priority_score": 34,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "users_and_customers",
        "label": "Geographic regions served",
        "unlocks_on": None,
    },
    {
        "key": "tooling.apis.api_authentication_method",
        "priority_score": 38,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "enum",
        "section": "tooling",
        "label": "API authentication method",
        "allowed_values": ["api_key", "oauth2", "jwt", "mtls", "none", "mixed"],
    },
    {
        "key": "risk_profile.incident_response_process",
        "priority_score": 40,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "risk_profile",
        "label": "Incident response process for AI failures",
        "unlocks_on": None,
    },
    {
        "key": "risk_profile.mitigations_in_place",
        "priority_score": 38,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "risk_profile",
        "label": "Risk mitigations currently in place",
        "unlocks_on": None,
    },
    {
        "key": "architecture.multi_agent.is_multi_agent",
        "priority_score": 30,
        "risk_level": "MEDIUM",
        "required": True,
        "answer_type": "boolean",
        "section": "architecture",
        "label": "Is multi-agent system",
        "unlocks_on": {
            "true": [
                "architecture.multi_agent.number_of_agents",
                "architecture.multi_agent.agent_communication_protocol",
            ]
        },
    },
    {
        "key": "models.embedding_model",
        "priority_score": 22,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "free_text",
        "section": "models",
        "label": "Embedding model used",
        "unlocks_on": None,
    },
    {
        "key": "models.secondary_models",
        "priority_score": 20,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "free_text",
        "section": "models",
        "label": "Secondary models (classifiers, rerankers)",
        "unlocks_on": None,
    },
    {
        "key": "tooling.tools",
        "priority_score": 48,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "tool_registry",
        "section": "tooling",
        "label": "Agent tools (name, purpose, access)",
        "context_hint": "Collect exact tool or API names, not generic categories.",
        "unlocks_on": None,
    },
    {
        "key": "data_assets.pii_categories",
        "priority_score": 30,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "multi_enum",
        "section": "data_assets",
        "label": "PII categories present",
        "allowed_values": [
            "name",
            "email",
            "phone",
            "address",
            "national_id",
            "passport",
            "dob",
            "tax_id",
            "bank_account",
            "card_number",
            "ssn",
            "income",
            "credit_score",
            "ip_address",
            "device_id",
            "cookies",
            "biometric",
            "health",
            "political_views",
            "religious_beliefs",
        ],
    },
    {
        "key": "knowledge_sources.knowledge_base_description",
        "priority_score": 25,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "free_text",
        "section": "knowledge_sources",
        "label": "Knowledge base and documents description",
        "unlocks_on": None,
    },
    {
        "key": "security.secrets_management",
        "priority_score": 28,
        "risk_level": "MEDIUM",
        "required": True,
        "answer_type": "free_text",
        "section": "security",
        "label": "Secrets management approach",
        "unlocks_on": None,
    },
    {
        "key": "compliance.data_retention_policy",
        "priority_score": 28,
        "risk_level": "MEDIUM",
        "required": True,
        "answer_type": "free_text",
        "section": "compliance",
        "label": "Data retention policy",
        "unlocks_on": None,
    },
    {
        "key": "compliance.cross_border_transfer",
        "priority_score": 22,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "boolean",
        "section": "compliance",
        "label": "Cross-border data transfer",
        "unlocks_on": None,
    },
    {
        "key": "risk_profile.risk_tolerance",
        "priority_score": 25,
        "risk_level": "MEDIUM",
        "required": True,
        "answer_type": "free_text",
        "section": "risk_profile",
        "label": "Risk tolerance level",
        "unlocks_on": None,
    },
    {
        "key": "system_access.entry_point_curl",
        "priority_score": 12,
        "risk_level": "LOW",
        "required": False,
        "answer_type": "url",
        "section": "system_access",
        "label": "System entry point / API endpoint",
        "unlocks_on": None,
    },
    {
        "key": "system_access.authentication_curl",
        "priority_score": 10,
        "risk_level": "LOW",
        "required": False,
        "answer_type": "free_text",
        "section": "system_access",
        "label": "Authentication curl example",
        "unlocks_on": None,
    },
    {
        "key": "knowledge_sources.document_uploads",
        "priority_score": 12,
        "risk_level": "LOW",
        "required": False,
        "answer_type": "document_upload",
        "section": "knowledge_sources",
        "label": "Policy and document uploads",
        "context_hint": "Upload internal AI, data handling, or other governance policy documents.",
        "unlocks_on": None,
    },
    {
        "key": "policies.internal_ai_policy",
        "priority_score": 44,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "policies",
        "label": "Internal AI usage policy",
        "context_hint": (
            "Ask for scope, permitted/prohibited AI uses, approved models, "
            "human review requirements, exceptions, and how the policy is enforced."
        ),
        "unlocks_on": None,
    },
    {
        "key": "policies.data_handling_policy",
        "priority_score": 44,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "policies",
        "label": "Data handling policy",
        "context_hint": (
            "Ask for data categories covered, retention, encryption, sharing rules, "
            "cross-border transfer, subject rights, and enforcement."
        ),
        "unlocks_on": None,
    },
    {
        "key": "policies.acceptable_use_policy",
        "priority_score": 42,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "policies",
        "label": "Acceptable use policy",
        "context_hint": (
            "Ask for who it applies to, allowed/prohibited behaviors, monitoring, "
            "violations, exceptions, and enforcement."
        ),
        "unlocks_on": None,
    },
    {
        "key": "policies.human_oversight_policy",
        "priority_score": 42,
        "risk_level": "HIGH",
        "required": True,
        "answer_type": "free_text",
        "section": "policies",
        "label": "Human oversight policy",
        "context_hint": (
            "Ask for when human approval is required, escalation paths, "
            "logging, accountability, and exceptions."
        ),
        "unlocks_on": None,
    },
    {
        "key": "policies.policy_document_refs",
        "priority_score": 18,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "free_text",
        "section": "policies",
        "label": "Policy document references",
        "context_hint": "Ask for titles, versions, owners, and where official policy documents live.",
        "unlocks_on": None,
    },
    {
        "key": "tooling.human_approval_config.approval_for",
        "priority_score": 28,
        "risk_level": "HIGH",
        "required": False,
        "answer_type": "multi_enum",
        "section": "tooling",
        "label": "Actions requiring human approval",
        "allowed_values": [
            "payments",
            "account_updates",
            "loan_approval",
            "kyc_verification",
            "large_transactions",
            "data_export",
            "customer_communication",
            "other",
        ],
        "unlocks_on": None,
    },
    {
        "key": "architecture.agentic.autonomy_level",
        "priority_score": 35,
        "risk_level": "HIGH",
        "required": False,
        "answer_type": "enum",
        "section": "architecture",
        "label": "Agent autonomy level",
        "allowed_values": [
            "fully_autonomous",
            "human_in_the_loop",
            "human_on_the_loop",
            "human_in_command",
        ],
        "unlocks_on": None,
    },
    {
        "key": "architecture.agentic.orchestration_pattern",
        "priority_score": 32,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "enum",
        "section": "architecture",
        "label": "Orchestration pattern",
        "allowed_values": ["sequential", "parallel", "hierarchical", "event_driven", "reactive", "mixed"],
        "unlocks_on": None,
    },
    {
        "key": "architecture.multi_agent.number_of_agents",
        "priority_score": 18,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "number",
        "section": "architecture",
        "label": "Number of agents",
        "unlocks_on": None,
    },
    {
        "key": "architecture.multi_agent.agent_communication_protocol",
        "priority_score": 18,
        "risk_level": "MEDIUM",
        "required": False,
        "answer_type": "enum",
        "section": "architecture",
        "label": "Agent communication protocol",
        "allowed_values": ["direct_api", "message_queue", "shared_memory", "event_bus", "custom"],
        "unlocks_on": None,
    },
]


def compute_priority_score(
    risk_level: RiskLevel,
    required: bool,
    section: str,
) -> int:
    risk = RISK_WEIGHTS.get(risk_level, 0)
    req = 10 if required else 0
    sec = SECTION_WEIGHTS.get(section, 5)
    return risk + req + sec


def _normalize_unlocks(raw: Any) -> dict[str, list[str]] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return {str(k).lower(): list(v) for k, v in raw.items()}
    return None


def build_queue_from_template() -> list[RiskQueueItem]:
    items: list[RiskQueueItem] = []
    for raw in PRIORITY_QUEUE_TEMPLATE:
        section = raw["section"]
        risk_level: RiskLevel = raw["risk_level"]
        required = raw["required"]
        score = raw.get("priority_score") or compute_priority_score(risk_level, required, section)
        items.append(
            RiskQueueItem(
                key=raw["key"],
                label=raw["label"],
                section=section,
                priority_score=score,
                risk_level=risk_level,
                required=required,
                answer_type=raw["answer_type"],
                allowed_values=raw.get("allowed_values"),
                unlocks_on=_normalize_unlocks(raw.get("unlocks_on")),
                context_hint=raw.get("context_hint"),
            )
        )
    items.sort(key=lambda x: x.priority_score, reverse=True)
    return items


def clone_session_queue() -> list[RiskQueueItem]:
    return copy.deepcopy(build_queue_from_template())


def queue_item_by_key(queue: list[RiskQueueItem], key: str) -> RiskQueueItem | None:
    for item in queue:
        if item.key == key:
            return item
    return None


def load_schema_field_keys() -> set[str]:
    path = Path(__file__).resolve().parents[2] / "jupiter_discovery_schema_v2.json"
    with path.open(encoding="utf-8") as fh:
        schema = json.load(fh)

    keys: set[str] = set()

    def walk(node: Any, prefix: str) -> None:
        if isinstance(node, dict) and "value" in node and "confidence" in node:
            keys.add(prefix)
            return
        if not isinstance(node, dict):
            return
        for k, child in node.items():
            if k == "discovery_state":
                continue
            child_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(child, list) and child and isinstance(child[0], dict):
                keys.add(child_prefix)
                continue
            walk(child, child_prefix)

    walk(schema, "")
    return keys


def validate_template_keys() -> list[str]:
    """Return orphan template keys not present in jupiter schema (excluding internal flags)."""
    schema_keys = load_schema_field_keys()
    orphans: list[str] = []
    for raw in PRIORITY_QUEUE_TEMPLATE:
        key = raw["key"]
        if key.startswith(INTERNAL_FLAG_PREFIX):
            continue
        if key not in schema_keys and key != "knowledge_sources.document_uploads":
            orphans.append(key)
    return orphans
