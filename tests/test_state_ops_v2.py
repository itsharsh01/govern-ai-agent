from __future__ import annotations

from agent.discovery_v2.models import FactPatch
from agent.discovery_v2.priority_queue import build_queue_from_template
from agent.discovery_v2.state_ops import (
    apply_patches,
    build_ui_hint,
    check_confidence,
    init_session_state,
    patches_from_structured_answers,
)


def test_apply_patch_pops_at_threshold():
    state = init_session_state("sess-ops")
    patches = [
        FactPatch(
            key=state.queue[0].key,
            value=True,
            confidence=0.9,
            source="customer_stated",
        )
    ]
    filled = apply_patches(state, patches)
    assert filled
    assert state.queue[0].key != patches[0].key
    assert state.filled_keys >= 1


def test_structured_patches_high_confidence():
    patches = patches_from_structured_answers(
        {"system_profile.industry": "banking"},
        turn=1,
    )
    assert patches[0].confidence == 0.95


def test_completion_pct_updates():
    state = init_session_state("sess-pct")
    assert state.completion_pct == 0.0
    assert state.total_keys == len(state.queue)


def test_build_ui_hint_tool_registry_and_document_upload():
    by_key = {i.key: i for i in build_queue_from_template()}
    tool_hint = build_ui_hint(by_key["tooling.tools"])
    assert tool_hint is not None
    assert tool_hint.interaction_type == "tool_registry"
    assert tool_hint.field_key == "tooling.tools"
    assert tool_hint.min_selections == 1

    doc_hint = build_ui_hint(by_key["knowledge_sources.document_uploads"])
    assert doc_hint is not None
    assert doc_hint.interaction_type == "document_upload"
    assert doc_hint.max_selections == 5
