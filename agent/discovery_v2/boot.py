from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from agent.discovery_v2.copy import DISCOVERY_GREETING, LLM_UNAVAILABLE_NOTICE
from agent.discovery_v2.llm import discovery_llm_available, llm_in_cooldown, llm_was_degraded
from agent.discovery_v2.models import TurnResponse
from agent.discovery_v2.session_store import SessionStore
from agent.discovery_v2.state_ops import build_ui_hint
from agent.discovery_v2.tools.generate_question import generate_question_tool, stream_generate_question

_store = SessionStore()


def _event(name: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"event": name, "data": data}


def iter_boot_events(customer_id: str | None = None) -> Iterator[dict[str, Any]]:
    yield _event("status", {"phase": "booting", "message": "Starting discovery session..."})

    session = _store.create_session(customer_id=customer_id)
    state = _store.get_state(session)
    if not state.queue:
        raise RuntimeError("Priority queue is empty")

    target = state.queue[0]
    state.current_key = target.key

    yield _event("greeting", {"content": DISCOVERY_GREETING})
    session["conversation"].append({"role": "assistant", "content": DISCOVERY_GREETING})

    notices: list[str] = []
    if not discovery_llm_available():
        notice = LLM_UNAVAILABLE_NOTICE
        if llm_in_cooldown():
            notice = (
                f"{LLM_UNAVAILABLE_NOTICE}\n\n"
                "(Groq rate limit — new API calls are paused briefly.)"
            )
        notices.append(notice)
        yield _event("notice", {"content": notice, "kind": "llm_unavailable"})
        session["conversation"].append({"role": "assistant", "content": notice})

    yield _event("status", {"phase": "generating", "message": "Preparing your first question..."})

    question = ""
    for phase, content in stream_generate_question(target, state, section_intro_needed=None):
        yield _event("assistant_message", {"content": content, "phase": phase})
        if phase == "final":
            question = content

    if not question:
        question = generate_question_tool(target, state, section_intro_needed=None)

    if llm_was_degraded() and LLM_UNAVAILABLE_NOTICE not in notices:
        notices.append(LLM_UNAVAILABLE_NOTICE)
        yield _event("notice", {"content": LLM_UNAVAILABLE_NOTICE, "kind": "llm_unavailable"})
        session["conversation"].append({"role": "assistant", "content": LLM_UNAVAILABLE_NOTICE})

    session["conversation"].append({"role": "assistant", "content": question})
    _store.set_state(session, state)
    _store.save_session(session)

    response = TurnResponse(
        session_id=session["session_id"],
        assistant_message=question,
        current_key=state.current_key,
        completion_pct=state.completion_pct,
        remaining_keys=state.remaining_keys,
        discovery_complete=False,
        ui_hint=build_ui_hint(target),
        notices=notices,
    )
    yield _event("done", response.model_dump(mode="json"))


def create_session(customer_id: str | None = None) -> TurnResponse:
    final: TurnResponse | None = None
    for event in iter_boot_events(customer_id=customer_id):
        if event["event"] == "done":
            final = TurnResponse.model_validate(event["data"])
    assert final is not None
    return final
