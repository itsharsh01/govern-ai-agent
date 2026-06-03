from __future__ import annotations

from agent.discovery_v2.models import FactPatch
from agent.discovery_v2.state_ops import (
    apply_patches,
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
