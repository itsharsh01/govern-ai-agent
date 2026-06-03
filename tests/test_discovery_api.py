from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agent.api.main import app
from agent.discovery.models import DiscoveryProgress, DiscoveryTurnResponse
from agent.discovery.models import GapKind, RankedGap


@pytest.fixture
def client():
    return TestClient(app)


def _sample_turn_response(session_id: str = "sess-api") -> DiscoveryTurnResponse:
    return DiscoveryTurnResponse(
        session_id=session_id,
        assistant_message="What business problem does your AI system solve?",
        discovery_progress=DiscoveryProgress(
            overall_completeness=0.1,
            overall_confidence=0.0,
            discovery_phase="initial",
            section_progress={},
            conversation_turns=0,
        ),
        current_understanding=[],
        remaining_gaps=[
            RankedGap(
                field_path="system_profile.business_purpose",
                section="system_profile",
                risk_score=1.0,
                kind=GapKind.MISSING,
                rationale="Opening discovery question",
            )
        ],
        discovery_complete=False,
    )


@patch("agent.api.routes.discovery.create_session")
def test_start_discovery_session(mock_create, client):
    mock_create.return_value = _sample_turn_response()
    response = client.post("/api/v1/discovery/sessions", json={})
    assert response.status_code == 201
    body = response.json()
    assert body["session_id"] == "sess-api"
    assert "assistant_message" in body


@patch("agent.api.routes.discovery.process_turn")
def test_post_discovery_message(mock_turn, client):
    mock_turn.return_value = _sample_turn_response()
    mock_turn.return_value.discovery_progress.conversation_turns = 1
    response = client.post(
        "/api/v1/discovery/sessions/sess-api/messages",
        json={"message": "We built a banking assistant"},
    )
    assert response.status_code == 200
    assert response.json()["discovery_progress"]["conversation_turns"] == 1


@patch("agent.api.routes.discovery._repository")
def test_get_digital_twin_not_complete_returns_404(mock_repo, client):
    mock_repo.load_session.return_value = {
        "session_id": "sess-api",
        "schema": {
            "discovery_state": {
                "discovery_complete": False,
            }
        },
        "completion_outputs": None,
    }
    response = client.get("/api/v1/discovery/sessions/sess-api/digital-twin")
    assert response.status_code == 404
