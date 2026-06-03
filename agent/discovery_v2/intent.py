from __future__ import annotations

import re

_CLARIFY = (
    re.compile(r"^what\s+is\b", re.I),
    re.compile(r"^what\s+are\b", re.I),
    re.compile(r"^explain\b", re.I),
    re.compile(r"^define\b", re.I),
    re.compile(r"^can\s+you\s+explain\b", re.I),
    re.compile(r"^help\s+me\s+understand\b", re.I),
)

_EXPLAINERS: dict[str, str] = {
    "security.output_filtering": (
        "Output filtering means guardrails that scan AI responses before they reach users — "
        "redacting PII, blocking policy violations, or enforcing format rules. "
        "When ready, describe what output filtering your system uses."
    ),
    "data_assets.pii_sent_to_external_llm": (
        "This means whether customer PII is included in prompts sent to third-party LLM APIs "
        "versus staying on-premises or tokenized."
    ),
    "knowledge_sources.uses_rag": (
        "RAG means the model retrieves relevant documents or knowledge chunks before answering, "
        "rather than relying only on training data."
    ),
}


def is_clarifying(message: str) -> bool:
    text = message.strip()
    return bool(text) and any(p.search(text) for p in _CLARIFY)


def build_clarification(current_key: str | None, message: str) -> str | None:
    if not is_clarifying(message):
        return None
    if not current_key:
        return (
            "I'm happy to clarify. Which governance topic should I explain — "
            "data handling, security controls, or tool access?"
        )
    if current_key in _EXPLAINERS:
        return _EXPLAINERS[current_key]
    label = current_key.split(".")[-1].replace("_", " ")
    return (
        f"In this discovery, '{label}' is an attribute we need to document for your governance profile. "
        f"Please share how your system handles it in practice when you're ready."
    )
