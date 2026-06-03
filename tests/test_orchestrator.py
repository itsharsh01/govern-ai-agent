from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent.discovery.models import ExtractedFact
from agent.discovery.orchestrator import DiscoveryOrchestrator
from agent.discovery.schema_utils import new_session_schema


@pytest.fixture
def orchestrator():
    orch = DiscoveryOrchestrator()
    orch.repository = MagicMock()
    return orch


def test_orchestrator_process_turn_extracts_facts_and_asks_one_question(orchestrator):
    schema = new_session_schema("sess-1")
    session = {
        "session_id": "sess-1",
        "customer_id": None,
        "schema": schema,
        "conversation": [],
        "completion_outputs": None,
        "created_at": "now",
        "updated_at": "now",
    }
    orchestrator.repository.load_session.return_value = session

    facts = [
        ExtractedFact(
            type="tool",
            field_path="tooling.tools",
            value="CRM",
            confidence=0.95,
            source_message="CRM and KYC API",
        ),
        ExtractedFact(
            type="framework",
            field_path="architecture.framework",
            value="langgraph",
            confidence=0.9,
            source_message="CRM and KYC API",
        ),
    ]
    with patch.object(orchestrator.fact_extractor, "extract", return_value=facts):
        response = orchestrator.process_turn("sess-1", "We use LangGraph with CRM and KYC API")

    assert response.session_id == "sess-1"
    assert response.discovery_complete is False
    assert "?" in response.assistant_message or len(response.assistant_message) > 20
    assert response.discovery_progress.conversation_turns == 1
    assert len(response.current_understanding) >= 1
    orchestrator.repository.save_session.assert_called_once()


def test_orchestrator_create_session_returns_opening_question(orchestrator):
    schema = new_session_schema("sess-new")
    session = {
        "session_id": "sess-new",
        "customer_id": None,
        "schema": schema,
        "conversation": [],
        "completion_outputs": None,
        "created_at": "now",
        "updated_at": "now",
    }
    orchestrator.repository.create_session.return_value = session

    response = orchestrator.create_session()
    assert response.session_id == "sess-new"
    assert response.discovery_progress.conversation_turns == 0
    assert len(response.assistant_message) > 10
