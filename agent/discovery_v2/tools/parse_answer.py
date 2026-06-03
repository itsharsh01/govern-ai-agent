from __future__ import annotations

import re
from typing import Any

from agent.discovery_v2.llm import discovery_llm_available, generate_json
from agent.discovery_v2.models import FactPatch, ParseAnswerResult, SessionState
from agent.discovery_v2.priority_queue import queue_item_by_key
from agent.discovery_v2.state_ops import already_known_summary

_YES = frozenset({"yes", "y", "yeah", "yep", "sure", "true", "correct", "affirmative", "we do", "it does"})
_NO = frozenset({"no", "n", "nope", "nah", "false", "negative", "we don't", "we do not"})

_PAYMENT_KW = ("payment", "wire", "transfer", "card")
_PII_KW = ("pii", "personal data", "customer data", "ssn", "national id")


def _parse_yes_no(text: str) -> bool | None:
    lower = text.strip().lower().rstrip(".")
    if lower in _YES or lower.startswith("yes"):
        return True
    if lower in _NO or lower.startswith("no"):
        return False
    return None


def _rule_patches(state: SessionState, user_answer: str, current_key: str | None) -> list[FactPatch]:
    patches: list[FactPatch] = []
    text = user_answer.strip()
    lower = text.lower()

    if current_key:
        item = queue_item_by_key(state.queue, current_key)
        if item and item.answer_type == "boolean":
            yn = _parse_yes_no(text)
            if yn is not None:
                patches.append(
                    FactPatch(key=current_key, value=yn, confidence=0.92, source="customer_stated")
                )
                return patches

    if "langgraph" in lower:
        patches.append(
            FactPatch(key="architecture.framework", value="langgraph", confidence=0.9, source="customer_stated")
        )
    if "langchain" in lower:
        patches.append(
            FactPatch(key="architecture.framework", value="langchain", confidence=0.88, source="customer_stated")
        )
    if re.search(r"\b(CRM|KYC|payment|AML)\b", text, re.I):
        for m in re.findall(r"\b(CRM|KYC|payment|AML)\b", text, re.I):
            patches.append(
                FactPatch(key="tooling.tools", value=m.upper(), confidence=0.9, source="customer_stated")
            )
    if "rag" in lower or "retrieval" in lower:
        patches.append(
            FactPatch(key="knowledge_sources.uses_rag", value=True, confidence=0.85, source="customer_stated")
        )

    if current_key and not patches and len(text) > 3:
        item = queue_item_by_key(state.queue, current_key)
        conf = 0.88 if item and item.answer_type == "free_text" else 0.8
        patches.append(
            FactPatch(key=current_key, value=text, confidence=conf, source="customer_stated")
        )

    return patches


def _detect_risk_flags(patches: list[FactPatch], user_answer: str) -> list[str]:
    flags: list[str] = []
    lower = user_answer.lower()
    for p in patches:
        if p.key == "data_assets.pii_sent_to_external_llm" and p.value is True:
            flags.append("pii_to_llm")
        if p.key == "architecture.agentic.is_agentic" and p.value is True:
            flags.append("autonomous_actions")
    if any(k in lower for k in _PAYMENT_KW):
        flags.append("payment_api")
    if any(k in lower for k in _PII_KW):
        flags.append("kyc_data_exposure")
    if "write" in lower or "approve" in lower:
        flags.append("write_operations")
    return list(dict.fromkeys(flags))


def parse_answer_tool(
    user_answer: str,
    state: SessionState,
) -> ParseAnswerResult:
    """ADK tool: extract fact patches from user message."""
    current_key = state.current_key
    patches = _rule_patches(state, user_answer, current_key)

    if discovery_llm_available() and (not patches or len(user_answer) > 80):
        item = queue_item_by_key(state.queue, current_key) if current_key else None
        known = already_known_summary(state)
        prompt = (
            f"Current field: {current_key}\n"
            f"Answer type: {item.answer_type if item else 'free_text'}\n"
            f"Allowed values: {item.allowed_values if item else None}\n"
            f"Known: {known}\n"
            f"User answer: {user_answer}\n"
            'Return JSON: {"patches":[{"key":"...","value":...,"confidence":0.0-1.0,"source":"customer_stated"}],'
            '"needs_cross_question":false,"cross_question_reason":null}'
        )
        data = generate_json(
            prompt,
            system="Extract governance discovery facts. Only include high-confidence fields.",
        )
        for raw in data.get("patches") or []:
            if not raw.get("key"):
                continue
            patches.append(
                FactPatch(
                    key=raw["key"],
                    value=raw.get("value"),
                    confidence=float(raw.get("confidence", 0.8)),
                    source=raw.get("source", "customer_stated"),
                )
            )
        if data.get("needs_cross_question"):
            return ParseAnswerResult(
                patches=patches,
                risk_flags_detected=_detect_risk_flags(patches, user_answer),
                needs_cross_question=True,
                cross_question_reason=data.get("cross_question_reason"),
            )

    needs_cross = False
    reason = None
    if current_key and current_key in state.discovered:
        entry = state.discovered[current_key]
        if entry.confidence < 0.75 and len(user_answer.strip()) < 15:
            needs_cross = True
            reason = "Answer was too brief for this field."

    for p in patches:
        if p.confidence < 0.75:
            needs_cross = True
            reason = reason or f"Low confidence on {p.key}"

    return ParseAnswerResult(
        patches=patches,
        risk_flags_detected=_detect_risk_flags(patches, user_answer),
        needs_cross_question=needs_cross,
        cross_question_reason=reason,
    )
