from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.audit import kg_context


def test_customer_instance_count_returns_zero_on_failure():
    with (
        patch("agent.audit.kg_context.Neo4jSettings.from_env", return_value=MagicMock()),
        patch("agent.audit.kg_context.neo4j_session") as mock_session,
    ):
        mock_session.side_effect = ConnectionError("neo4j down")
        assert kg_context.customer_instance_count("cust-1") == 0


def test_fetch_governance_context_returns_rows():
    mock_record = {
        "customer_instance": "My Agent",
        "agent_name": "Payment agent",
        "agent_purpose": "Payments",
        "regulation_name": "PCI-DSS",
        "regulation_description": "Card data rules",
    }
    mock_result = MagicMock()
    mock_result.__iter__ = lambda self: iter([mock_record])

    mock_neo4j = MagicMock()
    mock_neo4j.run.return_value = mock_result

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = lambda self: mock_neo4j
    mock_ctx.__exit__ = lambda *args: None

    with (
        patch("agent.audit.kg_context.Neo4jSettings.from_env", return_value=MagicMock()),
        patch("agent.audit.kg_context.neo4j_session", return_value=mock_ctx),
    ):
        rows = kg_context.fetch_governance_context("cust-1")

    assert len(rows) == 1
    assert rows[0]["regulation_name"] == "PCI-DSS"
