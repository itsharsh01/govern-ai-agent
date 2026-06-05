from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.knowledge_graph.customer_graph import propagate_can_access, write_instance_mappings
from agent.knowledge_graph.models import EntityMappingRecord


@patch("agent.knowledge_graph.customer_graph.Neo4jSettings.from_env")
@patch("agent.knowledge_graph.customer_graph.neo4j_session")
def test_propagate_can_access(mock_session_ctx, mock_from_env):
    mock_from_env.return_value = MagicMock()
    session = MagicMock()
    session.run.return_value.single.return_value = {"edges": 5}
    mock_session_ctx.return_value.__enter__.return_value = session

    count = propagate_can_access("cust-1")
    assert count == 5
    cypher = session.run.call_args[0][0]
    assert "CAN_ACCESS" in cypher
    assert session.run.call_args[1]["customer_id"] == "cust-1"


@patch("agent.knowledge_graph.customer_graph.Neo4jSettings.from_env")
@patch("agent.knowledge_graph.customer_graph.neo4j_session")
def test_write_instance_mappings(mock_session_ctx, mock_from_env):
    mock_from_env.return_value = MagicMock()
    session = MagicMock()
    session.run.return_value.single.return_value = {
        "instances_written": 1,
        "instance_of_edges": 1,
    }
    mock_session_ctx.return_value.__enter__.return_value = session

    stats = write_instance_mappings(
        "cust-1",
        [
            EntityMappingRecord(
                source_key="tools[0]",
                source_value="CustomerInsightEngine",
                instance_id="inst-1",
                ontology_node_id="neo4j-crm",
                ontology_name="CRM Tool",
                ontology_node_type="AgentTool",
                match_score=0.9,
                match_method="semantic",
                status="mapped",
                entity_type="tool",
            )
        ],
    )
    assert stats["instances_written"] == 1
    cypher = session.run.call_args[0][0]
    assert "INSTANCE_OF" in cypher
