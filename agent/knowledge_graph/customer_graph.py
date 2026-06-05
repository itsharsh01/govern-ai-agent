from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.knowledge_graph.client import neo4j_session
from agent.knowledge_graph.config import Neo4jSettings
from agent.knowledge_graph.models import EntityMappingRecord

SCHEMA_STATEMENTS = [
    """
    CREATE CONSTRAINT customer_graph_id IF NOT EXISTS
    FOR (g:CustomerGraph) REQUIRE g.customer_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT customer_instance_id IF NOT EXISTS
    FOR (i:CustomerInstance) REQUIRE (i.customer_id, i.instance_id) IS UNIQUE
    """,
    """
    CREATE INDEX customer_instance_customer_id IF NOT EXISTS
    FOR (i:CustomerInstance) ON (i.customer_id)
    """,
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(settings: Neo4jSettings | None = None) -> None:
    settings = settings or Neo4jSettings.from_env()
    with neo4j_session(settings) as session:
        for statement in SCHEMA_STATEMENTS:
            session.run(statement.strip())


def init_customer_graph(customer_id: str, settings: Neo4jSettings | None = None) -> dict[str, Any]:
    ensure_schema(settings)
    settings = settings or Neo4jSettings.from_env()
    now = _now_iso()
    with neo4j_session(settings) as session:
        record = session.run(
            """
            MERGE (g:CustomerGraph {customer_id: $customer_id})
            ON CREATE SET g.created_at = $now, g.status = 'initialized'
            ON MATCH SET g.updated_at = $now
            RETURN g.customer_id AS customer_id, g.status AS status, g.created_at AS created_at
            """,
            customer_id=customer_id,
            now=now,
        ).single()
    return dict(record or {"customer_id": customer_id, "status": "initialized"})


def delete_customer_instances(customer_id: str, settings: Neo4jSettings | None = None) -> int:
    settings = settings or Neo4jSettings.from_env()
    with neo4j_session(settings) as session:
        result = session.run(
            """
            MATCH (g:CustomerGraph {customer_id: $customer_id})-[:HAS_INSTANCE]->(i:CustomerInstance)
            DETACH DELETE i
            RETURN count(i) AS deleted
            """,
            customer_id=customer_id,
        ).single()
    return int(result["deleted"] if result else 0)


def write_instance_mappings(
    customer_id: str,
    mappings: list[EntityMappingRecord],
    settings: Neo4jSettings | None = None,
) -> dict[str, int]:
    if not mappings:
        return {"instances_written": 0, "instance_of_edges": 0}

    settings = settings or Neo4jSettings.from_env()
    rows = [
        {
            "instance_id": mapping.instance_id,
            "display_name": mapping.source_value,
            "source_key": mapping.source_key,
            "entity_type": mapping.entity_type,
            "ontology_node_id": mapping.ontology_node_id,
            "ontology_name": mapping.ontology_name,
            "match_score": mapping.match_score,
            "match_method": mapping.match_method,
            "mapping_id": mapping.instance_id,
        }
        for mapping in mappings
    ]

    with neo4j_session(settings) as session:
        result = session.run(
            """
            MATCH (g:CustomerGraph {customer_id: $customer_id})
            UNWIND $rows AS row
            MATCH (template:OntologyNode)
            WHERE elementId(template) = row.ontology_node_id
            MERGE (inst:CustomerInstance {
                customer_id: $customer_id,
                instance_id: row.instance_id
            })
            SET inst.display_name = row.display_name,
                inst.source_key = row.source_key,
                inst.entity_type = row.entity_type,
                inst.updated_at = $now
            MERGE (g)-[:HAS_INSTANCE]->(inst)
            MERGE (inst)-[m:INSTANCE_OF]->(template)
            SET m.match_score = row.match_score,
                m.match_method = row.match_method,
                m.mapping_id = row.mapping_id,
                m.ontology_name = row.ontology_name
            RETURN count(DISTINCT inst) AS instances_written,
                   count(m) AS instance_of_edges
            """,
            customer_id=customer_id,
            rows=rows,
            now=_now_iso(),
        ).single()

    return {
        "instances_written": int(result["instances_written"] if result else 0),
        "instance_of_edges": int(result["instance_of_edges"] if result else 0),
    }


def propagate_can_access(customer_id: str, settings: Neo4jSettings | None = None) -> int:
    settings = settings or Neo4jSettings.from_env()
    with neo4j_session(settings) as session:
        result = session.run(
            """
            MATCH (inst:CustomerInstance {customer_id: $customer_id})-[m:INSTANCE_OF]->(template:OntologyNode)
            MATCH (template)-[:CAN_ACCESS]->(asset:OntologyNode)
            MERGE (inst)-[a:CAN_ACCESS]->(asset)
            SET a.inherited_from = template.name,
                a.scope = coalesce(a.scope, 'inherited'),
                a.mapping_id = m.mapping_id
            RETURN count(a) AS edges
            """,
            customer_id=customer_id,
        ).single()
    return int(result["edges"] if result else 0)


def get_customer_graph_summary(
    customer_id: str,
    settings: Neo4jSettings | None = None,
) -> dict[str, Any]:
    settings = settings or Neo4jSettings.from_env()
    with neo4j_session(settings) as session:
        graph = session.run(
            """
            MATCH (g:CustomerGraph {customer_id: $customer_id})
            OPTIONAL MATCH (g)-[:HAS_INSTANCE]->(i:CustomerInstance)
            OPTIONAL MATCH (i)-[:INSTANCE_OF]->(t:OntologyNode)
            OPTIONAL MATCH (i)-[:CAN_ACCESS]->(a:OntologyNode)
            RETURN g.status AS status,
                   g.created_at AS created_at,
                   count(DISTINCT i) AS instance_count,
                   count(DISTINCT t) AS template_links,
                   count(DISTINCT a) AS can_access_targets
            """,
            customer_id=customer_id,
        ).single()

        instances = session.run(
            """
            MATCH (g:CustomerGraph {customer_id: $customer_id})-[:HAS_INSTANCE]->(i:CustomerInstance)
            OPTIONAL MATCH (i)-[:INSTANCE_OF]->(t:OntologyNode)
            OPTIONAL MATCH (i)-[:CAN_ACCESS]->(a:OntologyNode)
            RETURN i.display_name AS display_name,
                   i.source_key AS source_key,
                   i.entity_type AS entity_type,
                   t.name AS template_name,
                   collect(DISTINCT a.name) AS can_access
            ORDER BY i.display_name
            """,
            customer_id=customer_id,
        )

    return {
        "customer_id": customer_id,
        "graph": dict(graph or {}),
        "instances": [dict(row) for row in instances],
    }
