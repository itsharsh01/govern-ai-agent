from __future__ import annotations

from agent.discovery_v2.models import PeekQueueResult, SessionState
from agent.discovery_v2.state_ops import peek_queue


def peek_queue_tool(state: SessionState, previous_section: str | None = None) -> PeekQueueResult:
    """ADK tool: read next queue item without mutation."""
    return peek_queue(state, previous_section=previous_section)
