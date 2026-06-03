from __future__ import annotations

from agent.discovery_v2.models import FactPatch
from agent.discovery_v2.state_ops import init_session_state
from agent.discovery_v2.tools.check_confidence import check_confidence_tool
from agent.discovery_v2.tools.parse_answer import parse_answer_tool
from agent.discovery_v2.tools.peek_queue import peek_queue_tool


def test_parse_yes_no():
    state = init_session_state("sess-parse")
    key = state.current_key
    assert key is not None
    result = parse_answer_tool("yes", state)
    assert any(p.key == key and p.value is True for p in result.patches)


def test_peek_queue_first_item():
    state = init_session_state("sess-peek")
    peek = peek_queue_tool(state)
    assert peek.next_item is not None
    assert peek.remaining_count == len(state.queue)


def test_check_confidence_tool():
    state = init_session_state("sess-check")
    out = check_confidence_tool(state)
    assert out.completion_pct >= 0.0
