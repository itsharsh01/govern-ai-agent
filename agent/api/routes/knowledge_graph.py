from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from agent.api.kg_schemas import (
    EntityMappingResponse,
    KnowledgeGraphInitResponse,
    KnowledgeGraphMapRequest,
    KnowledgeGraphMapResponse,
    KnowledgeGraphSummaryResponse,
)
from agent.api.mongo.kg_repository import get_latest_mapping_run, save_mapping_run
from agent.api.storage import load_customer
from agent.discovery_v2.session_store import SessionStore
from agent.knowledge_graph.customer_graph import get_customer_graph_summary, init_customer_graph
from agent.knowledge_graph.kg_mapper import MappingRunResult, run_mapping

router = APIRouter(prefix="/customers", tags=["knowledge-graph"])
_session_store = SessionStore()


def _mapping_run_to_document(result: MappingRunResult) -> dict:
    return {
        "mapping_run_id": result.mapping_run_id,
        "customer_id": result.customer_id,
        "source": result.source,
        "entities": [asdict(entity) for entity in result.entities],
        "mapped_count": result.mapped_count,
        "skipped_count": result.skipped_count,
        "low_confidence": result.low_confidence,
        "neo4j_stats": result.neo4j_stats,
        "created_at": result.created_at,
    }


@router.post(
    "/{customer_id}/knowledge-graph/init",
    response_model=KnowledgeGraphInitResponse,
)
def initialize_customer_graph(customer_id: str) -> KnowledgeGraphInitResponse:
    load_customer(customer_id)
    graph = init_customer_graph(customer_id)
    return KnowledgeGraphInitResponse(
        customer_id=customer_id,
        status=str(graph.get("status", "initialized")),
        created_at=graph.get("created_at"),
    )


@router.post(
    "/{customer_id}/knowledge-graph/map",
    response_model=KnowledgeGraphMapResponse,
)
def map_customer_graph(
    customer_id: str,
    body: KnowledgeGraphMapRequest,
) -> KnowledgeGraphMapResponse:
    customer = load_customer(customer_id)
    discovered = None
    session_id = body.session_id
    if body.source == "discovery":
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required when source is discovery",
            )
        session = _session_store.load_session(session_id)
        if session.get("customer_id") and session["customer_id"] != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discovery session is linked to a different customer",
            )
        discovered = session["state"].get("discovered", {})

    try:
        result = run_mapping(
            customer_id,
            source_type=body.source,
            session_id=session_id,
            discovered=discovered,
            customer_record=customer if body.source == "customer" else None,
            replace_existing=body.replace_existing,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Knowledge graph mapping failed: {exc}",
        ) from exc

    save_mapping_run(_mapping_run_to_document(result))
    return KnowledgeGraphMapResponse(
        mapping_run_id=result.mapping_run_id,
        customer_id=result.customer_id,
        mapped_count=result.mapped_count,
        skipped_count=result.skipped_count,
        low_confidence=result.low_confidence,
        neo4j_stats=result.neo4j_stats,
        entities=[
            EntityMappingResponse(
                source_key=entity.source_key,
                source_value=entity.source_value,
                instance_id=entity.instance_id,
                ontology_node_id=entity.ontology_node_id,
                ontology_name=entity.ontology_name,
                ontology_node_type=entity.ontology_node_type,
                match_score=entity.match_score,
                match_method=entity.match_method,
                status=entity.status,
                entity_type=entity.entity_type,
            )
            for entity in result.entities
        ],
    )


@router.get(
    "/{customer_id}/knowledge-graph",
    response_model=KnowledgeGraphSummaryResponse,
)
def get_customer_knowledge_graph(customer_id: str) -> KnowledgeGraphSummaryResponse:
    load_customer(customer_id)
    try:
        summary = get_customer_graph_summary(customer_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to load knowledge graph summary: {exc}",
        ) from exc

    return KnowledgeGraphSummaryResponse(
        customer_id=customer_id,
        graph=summary.get("graph", {}),
        instances=summary.get("instances", []),
        last_mapping_run=get_latest_mapping_run(customer_id),
    )
