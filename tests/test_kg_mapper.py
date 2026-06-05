from __future__ import annotations

from unittest.mock import patch

from agent.knowledge_graph.entity_extractor import MappableEntity
from agent.knowledge_graph.kg_mapper import _match_entities, run_mapping
from agent.vector_database.search import OntologySearchHit


def test_match_entities_respects_threshold():
    entities = [
        MappableEntity(
            entity_id="e1",
            source_key="tooling.tools[0]",
            display_name="CustomerInsightEngine",
            search_text="Tool: CustomerInsightEngine. CRM lookup",
            entity_type="tool",
            node_types=("AgentTool",),
        ),
        MappableEntity(
            entity_id="e2",
            source_key="tooling.tools[1]",
            display_name="Unknown Widget",
            search_text="Tool: Unknown Widget",
            entity_type="tool",
            node_types=("AgentTool",),
        ),
    ]
    hits = {
        "e1": OntologySearchHit(
            query_id="e1",
            neo4j_id="neo4j-1",
            name="CRM Tool",
            node_type="AgentTool",
            score=0.91,
            match_method="semantic",
        ),
        "e2": OntologySearchHit(
            query_id="e2",
            neo4j_id="neo4j-2",
            name="Other Tool",
            node_type="AgentTool",
            score=0.55,
            match_method="semantic",
        ),
    }
    with patch("agent.knowledge_graph.kg_mapper.search_ontology_batch", return_value=hits):
        mapped, low_confidence, skipped = _match_entities(entities, score_threshold=0.72)

    assert len(mapped) == 1
    assert mapped[0].ontology_name == "CRM Tool"
    assert skipped == 1
    assert len(low_confidence) == 1


@patch("agent.knowledge_graph.kg_mapper.propagate_can_access", return_value=3)
@patch("agent.knowledge_graph.kg_mapper.write_instance_mappings", return_value={"instances_written": 1, "instance_of_edges": 1})
@patch("agent.knowledge_graph.kg_mapper.delete_customer_instances")
@patch("agent.knowledge_graph.kg_mapper.init_customer_graph", return_value={"status": "initialized"})
@patch("agent.knowledge_graph.kg_mapper.search_ontology_batch")
def test_run_mapping_discovery_source(
    mock_search,
    _mock_init,
    _mock_delete,
    _mock_write,
    _mock_propagate,
):
    mock_search.return_value = {
        "tool-0-abc": OntologySearchHit(
            query_id="tool-0-abc",
            neo4j_id="neo4j-crm",
            name="CRM Tool",
            node_type="AgentTool",
            score=0.95,
            match_method="semantic",
        )
    }
    discovered = {
        "tooling.tools": {
            "value": [
                {
                    "tool_name": "CustomerInsightEngine",
                    "tool_description": "CRM integration",
                    "access_required": "read",
                    "access_currently_has": "sandbox",
                }
            ]
        }
    }
    with patch("agent.knowledge_graph.kg_mapper.extract_from_discovery") as mock_extract:
        mock_extract.return_value = [
            MappableEntity(
                entity_id="tool-0-abc",
                source_key="tooling.tools[0]",
                display_name="CustomerInsightEngine",
                search_text="Tool: CustomerInsightEngine",
                entity_type="tool",
                node_types=("AgentTool",),
            )
        ]
        result = run_mapping(
            "cust-1",
            source_type="discovery",
            session_id="sess-1",
            discovered=discovered,
        )

    assert result.mapped_count == 1
    assert result.entities[0].ontology_name == "CRM Tool"
    assert result.neo4j_stats["can_access_edges"] == 3
