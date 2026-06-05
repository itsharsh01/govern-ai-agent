from __future__ import annotations

from typing import Any

from agent.api.mongo.client import get_database

KG_MAPPINGS_COLLECTION = "customer_kg_mappings"


def _collection():
    return get_database()[KG_MAPPINGS_COLLECTION]


def save_mapping_run(document: dict[str, Any]) -> dict[str, Any]:
    _collection().insert_one(document)
    document.pop("_id", None)
    return document


def get_latest_mapping_run(customer_id: str) -> dict[str, Any] | None:
    doc = _collection().find_one(
        {"customer_id": customer_id},
        sort=[("created_at", -1)],
    )
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


def list_mapping_runs(customer_id: str, limit: int = 10) -> list[dict[str, Any]]:
    cursor = (
        _collection()
        .find({"customer_id": customer_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    runs: list[dict[str, Any]] = []
    for doc in cursor:
        doc.pop("_id", None)
        runs.append(doc)
    return runs
