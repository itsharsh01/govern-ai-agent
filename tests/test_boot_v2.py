from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.discovery_v2.boot import create_session
from agent.discovery_v2.models import TurnResponse


@patch("agent.discovery_v2.boot._store")
@patch("agent.discovery_v2.boot.generate_question_tool", return_value="What is your business purpose?")
def test_create_session_returns_question(mock_gen, mock_store):
    from agent.discovery_v2.state_ops import init_session_state

    state = init_session_state("sess-boot")
    session = {
        "session_id": "sess-boot",
        "customer_id": None,
        "state": state.model_dump(mode="json"),
        "conversation": [],
        "completion_outputs": None,
    }
    mock_store.find_session_for_customer.return_value = None
    mock_store.create_session.return_value = session
    mock_store.get_state.return_value = state

    resp = create_session()
    assert isinstance(resp, TurnResponse)
    assert resp.assistant_message
    assert resp.current_key == state.current_key
    mock_store.save_session.assert_called_once()
