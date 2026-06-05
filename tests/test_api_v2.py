from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from agent.api.main import app
from agent.discovery_v2.models import TurnResponse, UIHint


@pytest.fixture
def client():
    return TestClient(app)


@patch("agent.api.routes.discovery_v2.create_session")
def test_start_session_v2(mock_create, client):
    mock_create.return_value = TurnResponse(
        session_id="sess-v2",
        assistant_message="Hello, what problem does your AI solve?",
        current_key="system_profile.business_purpose",
        completion_pct=0.0,
        remaining_keys=40,
        ui_hint=UIHint(
            interaction_type="text",
            field_key="system_profile.business_purpose",
            label="Business purpose",
        ),
    )
    res = client.post("/api/v2/discovery/sessions", json={})
    assert res.status_code == 201
    assert res.json()["session_id"] == "sess-v2"


@patch("agent.api.routes.discovery_v2.run_turn")
def test_post_turn_v2(mock_turn, client):
    mock_turn.return_value = TurnResponse(
        session_id="sess-v2",
        assistant_message="Next question?",
        current_key="models.primary_llm.provider",
        completion_pct=0.05,
        remaining_keys=38,
    )
    res = client.post(
        "/api/v2/discovery/sessions/sess-v2/turns",
        json={"message": "We use OpenAI"},
    )
    assert res.status_code == 200
    assert "assistant_message" in res.json()


@patch("agent.api.routes.discovery_v2._status_for_customer")
@patch("agent.api.routes.auth.load_customer")
@patch("agent.api.routes.auth.decode_access_token", return_value={"sub": "cust-1"})
def test_get_customer_discovery(mock_decode, mock_load_customer, mock_status, client):
    from agent.api.discovery_schemas_v2 import CustomerDiscoveryStatusResponse
    from agent.api.schemas import CustomerRecord

    mock_load_customer.return_value = CustomerRecord(
        id="cust-1",
        name="Test",
        email="test@example.com",
    )
    mock_status.return_value = CustomerDiscoveryStatusResponse(
        customer_id="cust-1",
        session_id="sess-1",
        discovery_complete=True,
        completion_pct=1.0,
        remaining_keys=0,
        current_key=None,
    )
    res = client.get(
        "/api/v2/discovery/customers/cust-1/discovery",
        headers={"Authorization": "Bearer token"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["session_id"] == "sess-1"
    assert body["discovery_complete"] is True
