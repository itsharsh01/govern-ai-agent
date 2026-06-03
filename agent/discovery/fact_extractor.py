from __future__ import annotations

import json
import os
import re
from typing import Any

from agent.discovery.llm_config import discovery_llm_enabled
from agent.discovery.models import ExtractedFact, FactExtractionResult
from agent.discovery.templates import FACT_TYPE_MAP

FRAMEWORK_ALIASES = {
    "langgraph": "langgraph",
    "lang chain": "langchain",
    "langchain": "langchain",
    "llamaindex": "llamaindex",
    "autogen": "autogen",
    "crewai": "crewai",
}

USE_CASE_KEYWORDS = {
    "banking": "banking_assistant",
    "kyc": "kyc_assistant",
    "loan": "loan_assistant",
    "support": "customer_support_agent",
    "investment": "investment_advisor",
    "fraud": "fraud_detection",
    "rag": "agentic_rag",
}

_YES_REPLIES = frozenset(
    {"yes", "y", "yeah", "yep", "sure", "correct", "true", "affirmative", "we do", "it does"}
)
_NO_REPLIES = frozenset(
    {"no", "n", "nope", "nah", "false", "negative", "we don't", "we do not", "it doesn't", "it does not"}
)


def _is_short_reply(message: str) -> bool:
    return len(message.strip()) <= 40


def _parse_yes_no(message: str) -> bool | None:
    lower = message.strip().lower().rstrip(".")
    if lower in _YES_REPLIES:
        return True
    if lower in _NO_REPLIES:
        return False
    if lower.startswith("yes"):
        return True
    if lower.startswith("no"):
        return False
    return None


def _contextual_extract(schema: dict[str, Any], message: str) -> list[ExtractedFact]:
    """Map short affirmations to the field Jupiter just asked about."""
    ctx = schema.get("discovery_state", {}).get("next_question_context") or {}
    target_field = ctx.get("target_field")
    if not target_field:
        return []

    yn = _parse_yes_no(message)
    if yn is None:
        return []

    return [
        ExtractedFact(
            type="contextual_reply",
            field_path=target_field,
            value=yn,
            confidence=0.92,
            source_message=message.strip(),
        )
    ]


def _resolve_field_path(fact_type: str, explicit_path: str | None) -> str | None:
    if explicit_path:
        return explicit_path
    mapped = FACT_TYPE_MAP.get(fact_type)
    if isinstance(mapped, list):
        return mapped[0]
    return mapped


def _rule_based_extract(message: str) -> list[ExtractedFact]:
    text = message.strip()
    lower = text.lower()
    facts: list[ExtractedFact] = []

    for alias, framework in FRAMEWORK_ALIASES.items():
        if alias in lower:
            facts.append(
                ExtractedFact(
                    type="framework",
                    field_path="architecture.framework",
                    value=framework,
                    confidence=0.9,
                    source_message=text,
                )
            )
            facts.append(
                ExtractedFact(
                    type="is_agentic",
                    field_path="architecture.agentic.is_agentic",
                    value=True,
                    confidence=0.75,
                    source_message=text,
                )
            )
            break

    if "banking" in lower or "fintech" in lower or "financial" in lower:
        facts.append(
            ExtractedFact(
                type="industry",
                field_path="system_profile.industry",
                value="banking",
                confidence=0.7,
                source_message=text,
            )
        )

    for keyword, use_case in USE_CASE_KEYWORDS.items():
        if keyword in lower:
            facts.append(
                ExtractedFact(
                    type="primary_use_case",
                    field_path="system_profile.primary_use_case",
                    value=use_case,
                    confidence=0.75,
                    source_message=text,
                )
            )
            break

    tool_patterns = re.findall(
        r"\b(CRM|KYC(?:\s+API)?|payment(?:\s+API)?|core banking|AML|sanctions)\b",
        text,
        flags=re.IGNORECASE,
    )
    for match in tool_patterns:
        facts.append(
            ExtractedFact(
                type="tool",
                field_path="tooling.tools",
                value=match.strip(),
                confidence=0.95,
                source_message=text,
            )
        )

    if "rag" in lower or "retrieval" in lower or "knowledge base" in lower:
        facts.append(
            ExtractedFact(
                type="uses_rag",
                field_path="knowledge_sources.uses_rag",
                value=True,
                confidence=0.85,
                source_message=text,
            )
        )

    if len(text) > 20 and not facts:
        facts.append(
            ExtractedFact(
                type="business_purpose",
                field_path="system_profile.business_purpose",
                value=text,
                confidence=0.8,
                source_message=text,
            )
        )
        facts.append(
            ExtractedFact(
                type="system_description",
                field_path="system_profile.system_description",
                value=text,
                confidence=0.75,
                source_message=text,
            )
        )

    return facts


def _structured_llm():
    if not discovery_llm_enabled():
        return None

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    model_name = os.getenv("DISCOVERY_LLM_MODEL", "gemini-2.0-flash")
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You extract structured governance discovery facts from customer messages. "
                "Return multiple facts when present. Use field_path when you know the schema path. "
                "Allowed types include: tool, framework, industry, primary_use_case, business_purpose, "
                "system_description, uses_rag, is_agentic, model_name, model_provider, data_type, "
                "pii_category, human_approval, authentication, authorization, regulation, policy.",
            ),
            (
                "human",
                "Current partial state:\n{state_summary}\n\nCustomer message:\n{message}",
            ),
        ]
    )
    return prompt | llm.with_structured_output(FactExtractionResult)


def extractor_available() -> bool:
    return discovery_llm_enabled()


def _state_summary(schema: dict[str, Any]) -> str:
    state = schema["discovery_state"]
    known = state.get("known_facts", [])[-8:]
    ctx = state.get("next_question_context") or {}
    parts: list[str] = []
    if ctx.get("target_field"):
        parts.append(
            f"Last question targeted field: {ctx['target_field']}. "
            f"Question: {ctx.get('question_text') or ''}"
        )
    if known:
        parts.append("Known facts: " + json.dumps(known, default=str))
    else:
        parts.append("No facts collected yet.")
    return "\n".join(parts)


class FactExtractionEngine:
    def extract(self, schema: dict[str, Any], message: str) -> list[ExtractedFact]:
        contextual = _contextual_extract(schema, message)
        if contextual and _is_short_reply(message):
            return contextual

        chain = _structured_llm()
        if chain is None:
            merged = _rule_based_extract(message)
            return contextual + merged if contextual else merged

        try:
            result: FactExtractionResult = chain.invoke(
                {"state_summary": _state_summary(schema), "message": message}
            )
            facts = result.facts
        except Exception:
            merged = _rule_based_extract(message)
            return contextual + merged if contextual else merged

        normalized: list[ExtractedFact] = []
        for fact in facts:
            path = _resolve_field_path(fact.type, fact.field_path)
            if not path:
                continue
            normalized.append(
                ExtractedFact(
                    type=fact.type,
                    field_path=path,
                    value=fact.value,
                    confidence=fact.confidence,
                    source_message=message,
                )
            )
        if contextual:
            normalized = contextual + normalized
        return normalized or _rule_based_extract(message)
