from __future__ import annotations

import json
from collections.abc import Iterator

from agent.discovery_v2.llm import (
    discovery_llm_available,
    generate_text,
    reset_llm_status,
    stream_generate_text,
)
from agent.discovery_v2.models import RiskQueueItem, SessionState
from agent.discovery_v2.state_ops import already_known_summary


def _build_prompt(
    target_item: RiskQueueItem,
    state: SessionState,
    *,
    is_cross_question: bool = False,
    section_intro_needed: str | None = None,
) -> str:
    history = state.turn_history[-state.max_history_turns :]
    known = already_known_summary(state)
    intro = ""
    if section_intro_needed:
        intro = (
            f"Introduce the new topic area ({section_intro_needed}) in one short phrase, "
            "then ask the question. "
        )
    instruction = (
        "You are a senior AI governance consultant conducting discovery. "
        "Generate exactly ONE concise professional question (max 2 sentences). "
        "Do not reveal schema field names or internal keys. "
        "Reference what the customer already shared when relevant. "
    )
    if is_cross_question:
        instruction += "The prior answer was unclear — ask a focused follow-up on the same topic. "
    instruction += intro
    return (
        f"{instruction}\n\n"
        f"Target topic: {target_item.label}\n"
        f"Risk level: {target_item.risk_level}\n"
        f"Expected answer type: {target_item.answer_type}\n"
        f"Already known: {json.dumps(known, default=str)}\n"
        f"Recent turns: {json.dumps([h.model_dump() for h in history], default=str)}\n"
    )


def fallback_question(item: RiskQueueItem) -> str:
    label = item.label
    if item.answer_type == "boolean":
        return f"Does your system involve {label}? Please answer yes or no."
    if item.allowed_values:
        return f"Regarding {label}, which option best applies to your system?"
    return f"Could you describe {label} for your AI system?"


def generate_question_tool(
    target_item: RiskQueueItem,
    state: SessionState,
    *,
    is_cross_question: bool = False,
    section_intro_needed: str | None = None,
) -> str:
    """ADK tool: natural language question for target queue item."""
    preview = fallback_question(target_item)
    if not discovery_llm_available():
        return preview
    prompt = _build_prompt(
        target_item,
        state,
        is_cross_question=is_cross_question,
        section_intro_needed=section_intro_needed,
    )
    text = generate_text(prompt)
    return text or preview


def stream_generate_question(
    target_item: RiskQueueItem,
    state: SessionState,
    *,
    is_cross_question: bool = False,
    section_intro_needed: str | None = None,
) -> Iterator[tuple[str, str]]:
    """
    Yield (phase, content) for SSE: delta chunks while generating, then final.
    Template fallback is only sent on final when LLM is off or fails (never as preview).
    """
    preview = fallback_question(target_item)
    reset_llm_status()

    if not discovery_llm_available():
        yield ("final", preview)
        return

    prompt = _build_prompt(
        target_item,
        state,
        is_cross_question=is_cross_question,
        section_intro_needed=section_intro_needed,
    )
    parts: list[str] = []
    for chunk in stream_generate_text(prompt):
        parts.append(chunk)
        yield ("delta", chunk)

    full = "".join(parts).strip() or preview
    yield ("final", full)
