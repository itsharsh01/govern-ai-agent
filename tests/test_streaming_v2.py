from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from agent.api.main import app
from agent.discovery_v2.models import TurnResponse, UIHint


@pytest.fixture
def client():
    return TestClient(app)


def _sample_turn() -> TurnResponse:
    return TurnResponse(
        session_id="sess-stream",
        assistant_message="What problem does your AI system solve?",
        current_key="system_profile.business_purpose",
        completion_pct=0.0,
        remaining_keys=40,
        ui_hint=UIHint(
            interaction_type="text",
            field_key="system_profile.business_purpose",
            label="Business purpose",
        ),
    )


@patch("agent.api.routes.discovery_v2.iter_boot_events")
def test_session_stream_emits_events(mock_iter, client):
    turn = _sample_turn()

    def events():
        yield {"event": "status", "data": {"phase": "booting", "message": "Starting..."}}
        yield {"event": "assistant_message", "data": {"content": "Full ", "phase": "delta"}}
        yield {"event": "assistant_message", "data": {"content": "question?", "phase": "final"}}
        yield {"event": "done", "data": turn.model_dump(mode="json")}

    mock_iter.return_value = events()

    with client.stream("POST", "/api/v2/discovery/sessions/stream", json={}) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())

    assert "status" in body
    assert "delta" in body or "final" in body
    assert body.index("done") > 0
    mock_iter.assert_called_once()


@patch("agent.api.routes.discovery_v2.iter_turn_events")
def test_turn_stream_emits_events(mock_iter, client):
    turn = _sample_turn()
    turn.assistant_message = "Next question?"

    def events():
        yield {"event": "status", "data": {"phase": "processing", "message": "Processing..."}}
        yield {"event": "progress", "data": {"completion_pct": 0.05, "remaining_keys": 38}}
        yield {"event": "assistant_message", "data": {"content": "Draft", "phase": "preview"}}
        yield {"event": "done", "data": turn.model_dump(mode="json")}

    mock_iter.return_value = events()

    with client.stream(
        "POST",
        "/api/v2/discovery/sessions/sess-stream/turns/stream",
        json={"message": "We use OpenAI"},
    ) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())

    assert "progress" in body
    assert "done" in body
