from __future__ import annotations

from agent.discovery_v2.state_ops import (
    apply_patches,
    init_session_state,
    patches_from_structured_answers,
)
from agent.discovery_v2.tools.parse_answer import (
    _merge_tool_registry,
    _normalize_tool_entry,
    _policy_needs_detail,
)


def test_normalize_tool_entry_accepts_aliases():
    entry = _normalize_tool_entry(
        {
            "name": "crm_lookup",
            "description": "Fetch customer",
            "access_required": "read",
            "access_granted": "read",
        }
    )
    assert entry is not None
    assert entry["tool_name"] == "crm_lookup"
    assert entry["tool_description"] == "Fetch customer"
    assert entry["access_currently_has"] == "read"


def test_merge_tool_registry_dedupes_by_name():
    existing = [{"tool_name": "A", "tool_description": "", "access_required": "", "access_currently_has": ""}]
    new = [
        {"tool_name": "a", "tool_description": "updated", "access_required": "", "access_currently_has": ""},
        {"tool_name": "B", "tool_description": "", "access_required": "", "access_currently_has": ""},
    ]
    merged = _merge_tool_registry(existing, new)
    names = {t["tool_name"].lower() for t in merged}
    assert names == {"a", "b"}
    assert merged[0]["tool_name"] == "A"


def test_policy_needs_detail_for_short_answer():
    needs, msg = _policy_needs_detail("policies.internal_ai_policy", "We have a policy.")
    assert needs is True
    assert msg is not None


def test_policy_document_refs_skips_detail_check():
    needs, _ = _policy_needs_detail("policies.policy_document_refs", "short")
    assert needs is False


def test_structured_tool_registry_patch_applies():
    tools = [
        {
            "tool_name": "stripe_create_payment",
            "tool_description": "Creates payment intents",
            "access_required": "write payments",
            "access_currently_has": "sandbox",
        }
    ]
    patches = patches_from_structured_answers({"tooling.tools": tools}, turn=1)
    state = init_session_state("sess-tools")
    apply_patches(state, patches)
    entry = state.discovered.get("tooling.tools")
    assert entry is not None
    assert entry.value == tools
    assert entry.confidence >= 0.9
