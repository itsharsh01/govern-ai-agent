from __future__ import annotations

from agent.discovery_v2.models import CheckConfidenceResult, SessionState
from agent.discovery_v2.state_ops import check_confidence


def check_confidence_tool(state: SessionState) -> CheckConfidenceResult:
    """ADK tool: evaluate pop / completion after patches applied."""
    return check_confidence(state)
