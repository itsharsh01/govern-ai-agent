from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from agent.api.main import app
from agent.api.schemas import CustomerRecord
from agent.knowledge_graph.kg_mapper import MappingRunResult
from agent.knowledge_graph.models import EntityMappingRecord


@pytest.fixture
def client():
    return TestClient(app)


@patch("agent.api.routes.knowledge_graph.init_customer_graph")
@patch("agent.api.routes.knowledge_graph.load_customer")
def test_init_customer_graph(mock_load, mock_init, client):
    mock_load.return_value = CustomerRecord(name="Acme", email="ops@acme.com")
    mock_init.return_value = {
        "customer_id": "cust-1",
        "status": "initialized",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    res = client.post("/api/v1/customers/cust-1/knowledge-graph/init")
    assert res.status_code == 200
    assert res.json()["status"] == "initialized"


@patch("agent.api.routes.knowledge_graph.save_mapping_run")
@patch("agent.api.routes.knowledge_graph.run_mapping")
@patch("agent.api.routes.knowledge_graph.load_customer")
def test_map_customer_graph(mock_load, mock_run, _mock_save, client):
    mock_load.return_value = CustomerRecord(name="Acme", email="ops@acme.com")
    mock_run.return_value = MappingRunResult(
        mapping_run_id="run-1",
        customer_id="cust-1",
        source={"type": "customer"},
        entities=[
            EntityMappingRecord(
                source_key="tools[0]",
                source_value="CustomerInsightEngine",
                instance_id="inst-1",
                ontology_node_id="neo4j-1",
                ontology_name="CRM Tool",
                ontology_node_type="AgentTool",
                match_score=0.93,
                match_method="semantic",
                status="mapped",
                entity_type="tool",
            )
        ],
        mapped_count=1,
        skipped_count=0,
        low_confidence=[],
        neo4j_stats={"instances_written": 1, "instance_of_edges": 1, "can_access_edges": 3},
        created_at="2026-01-01T00:00:00+00:00",
    )
    res = client.post(
        "/api/v1/customers/cust-1/knowledge-graph/map",
        json={"source": "customer", "replace_existing": False},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["mapping_run_id"] == "run-1"
    assert body["mapped_count"] == 1
    assert body["entities"][0]["ontology_name"] == "CRM Tool"
