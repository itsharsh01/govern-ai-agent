from __future__ import annotations

FACT_TYPE_MAP: dict[str, str | list[str]] = {
    "tool": "tooling.tools",
    "api": "tooling.apis.api_list",
    "framework": "architecture.framework",
    "system_type": "architecture.system_type",
    "industry": "system_profile.industry",
    "primary_use_case": "system_profile.primary_use_case",
    "business_purpose": "system_profile.business_purpose",
    "system_description": "system_profile.system_description",
    "model_provider": "models.primary_llm.provider",
    "model_name": "models.primary_llm.model_name",
    "data_type": "data_assets.data_types_processed",
    "pii_category": "data_assets.pii_categories",
    "uses_rag": "knowledge_sources.uses_rag",
    "is_agentic": "architecture.agentic.is_agentic",
    "is_multi_agent": "architecture.multi_agent.is_multi_agent",
    "autonomy_level": "architecture.agentic.autonomy_level",
    "human_approval": "tooling.human_approval_config.human_approval_required",
    "authentication": "security.authentication_method",
    "authorization": "security.authorization_model",
    "regulation": "compliance.applicable_regulations",
    "policy": "policies.internal_ai_policy",
}

SECTION_CATEGORY_WEIGHT: dict[str, float] = {
    "data_assets": 1.0,
    "tooling": 0.9,
    "architecture": 0.85,
    "knowledge_sources": 0.75,
    "security": 0.7,
    "compliance": 0.65,
    "policies": 0.6,
    "risk_profile": 0.55,
    "models": 0.5,
    "system_profile": 0.45,
    "users_and_customers": 0.4,
    "system_access": 0.2,
}

FIELD_BOOST: dict[str, float] = {
    "data_assets.pii_categories": 1.0,
    "data_assets.pii_sent_to_external_llm": 1.0,
    "data_assets.sensitive_financial_data": 0.95,
    "tooling.human_approval_config.human_approval_required": 0.9,
    "tooling.human_approval_config.approval_for": 0.85,
    "architecture.agentic.is_agentic": 0.8,
    "architecture.agentic.autonomy_level": 0.8,
    "knowledge_sources.uses_rag": 0.75,
    "security.audit_logging_enabled": 0.7,
    "security.output_filtering": 0.7,
    "compliance.consent_management": 0.65,
}

INFORMATION_GAIN_FIELDS: frozenset[str] = frozenset(
    {
        "architecture.agentic.is_agentic",
        "knowledge_sources.uses_rag",
        "architecture.multi_agent.is_multi_agent",
        "data_assets.sensitive_financial_data",
    }
)

QUESTION_TEMPLATES: dict[str, str] = {
    "system_profile.business_purpose": (
        "What business problem does your AI system solve, and who relies on it day to day?"
    ),
    "system_profile.system_description": (
        "Could you describe what the system does in practice — its main workflows and outputs?"
    ),
    "system_profile.industry": "Which financial services segment best describes your organization?",
    "system_profile.primary_use_case": "What is the primary use case for this AI system?",
    "data_assets.pii_categories": (
        "To understand possible data exposure risks, what categories of customer "
        "information can the assistant access?"
    ),
    "data_assets.pii_sent_to_external_llm": (
        "Does any customer PII or sensitive data get sent to external LLM providers? "
        "If so, which data types?"
    ),
    "data_assets.sensitive_financial_data": (
        "Does the system process sensitive financial data such as account balances, "
        "transactions, or payment details?"
    ),
    "data_assets.data_types_processed": (
        "What types of data does the system process — for example customer PII, "
        "transaction history, or KYC documents?"
    ),
    "tooling.human_approval_config.human_approval_required": (
        "Are there actions the agent can take that require human approval before execution?"
    ),
    "tooling.human_approval_config.approval_for": (
        "Which high-impact actions require human approval — payments, account updates, "
        "loan decisions, or data exports?"
    ),
    "architecture.agentic.is_agentic": (
        "Does the system autonomously decide which tools or APIs to call, "
        "or does it follow a fixed workflow?"
    ),
    "architecture.agentic.autonomy_level": (
        "How much autonomy does the agent have — fully autonomous, human-in-the-loop, "
        "or human-on-the-loop?"
    ),
    "architecture.framework": "Which agent or LLM framework powers the system?",
    "knowledge_sources.uses_rag": (
        "Does the system retrieve information from documents or a knowledge base (RAG) "
        "before responding?"
    ),
    "knowledge_sources.knowledge_base_description": (
        "What documents or knowledge sources does the system retrieve from, "
        "and how often are they updated?"
    ),
    "models.primary_llm.model_name": "Which LLM model(s) does the system use in production?",
    "models.primary_llm.provider": "Which provider hosts your primary LLM — OpenAI, Google, Anthropic, or other?",
    "security.authentication_method": (
        "How are users and agents authenticated when accessing the system?"
    ),
    "security.authorization_model": (
        "What authorization model controls what data and tools each user or agent can access?"
    ),
    "security.audit_logging_enabled": (
        "Is audit logging enabled for agent actions, tool calls, and data access?"
    ),
    "compliance.applicable_regulations": (
        "Which regulations apply to this system — GDPR, PCI-DSS, RBI guidelines, or others?"
    ),
    "policies.internal_ai_policy": (
        "Do you have an internal AI usage or governance policy that governs this system?"
    ),
    "risk_profile.incident_response_process": (
        "What is your incident response process if the AI system behaves unexpectedly "
        "or exposes sensitive data?"
    ),
}

DEFAULT_QUESTION_TEMPLATE = (
    "To complete our governance assessment, could you tell me about {field_label}?"
)

PAYMENT_KEYWORDS = frozenset(
    {"payment", "ach", "wire", "transfer", "card", "transaction", "billing"}
)
PII_KEYWORDS = frozenset(
    {"pii", "customer data", "personal", "ssn", "aadhaar", "pan", "kyc", "crm"}
)
WRITE_KEYWORDS = frozenset(
    {"write", "update", "delete", "approve", "submit", "initiate", "execute"}
)
