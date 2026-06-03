from __future__ import annotations

from agent.discovery_v2.priority_queue import (
    build_queue_from_template,
    clone_session_queue,
    compute_priority_score,
    validate_template_keys,
)


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


def test_template_orphans_acceptable():
    orphans = validate_template_keys()
    assert "knowledge_sources.document_uploads" in orphans or len(orphans) == 0
