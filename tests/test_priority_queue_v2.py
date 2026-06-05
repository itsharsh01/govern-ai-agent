from __future__ import annotations

from agent.discovery_v2.priority_queue import (
    SECTION_WEIGHTS,
    build_queue_from_template,
    clone_session_queue,
    compute_priority_score,
    validate_template_keys,
)


def _queue_item(key: str):
    for item in build_queue_from_template():
        if item.key == key:
            return item
    raise AssertionError(f"missing queue item: {key}")


def test_queue_sorted_descending():
    queue = build_queue_from_template()
    scores = [item.priority_score for item in queue]
    assert scores == sorted(scores, reverse=True)
    assert queue[0].key == "data_assets.pii_sent_to_external_llm"


def test_clone_is_independent():
    a = clone_session_queue()
    b = clone_session_queue()
    a.pop()
    assert len(a) < len(b)


def test_compute_priority_score():
    assert compute_priority_score("CRITICAL", True, "data_assets") == 62


def test_schema_aligned_policy_and_tool_keys():
    orphans = validate_template_keys()
    for key in (
        "tooling.tools",
        "policies.internal_ai_policy",
        "policies.data_handling_policy",
        "policies.acceptable_use_policy",
        "policies.human_oversight_policy",
        "policies.policy_document_refs",
    ):
        assert key not in orphans


def test_policies_section_weight_raised():
    assert SECTION_WEIGHTS["policies"] >= 16


def test_tooling_tools_uses_tool_registry():
    item = _queue_item("tooling.tools")
    assert item.answer_type == "tool_registry"
    assert item.required is True
    assert item.priority_score >= 45
    assert item.context_hint


def test_policies_queue_items_have_context_hints():
    for key in (
        "policies.internal_ai_policy",
        "policies.data_handling_policy",
        "policies.acceptable_use_policy",
        "policies.human_oversight_policy",
    ):
        item = _queue_item(key)
        assert item.required is True
        assert item.context_hint
        assert item.priority_score >= 40
