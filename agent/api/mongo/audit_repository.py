from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.api.mongo.client import get_database

AUDIT_SANDBOX_COLLECTION = "audit_sandbox_configs"


def _collection():
    return get_database()[AUDIT_SANDBOX_COLLECTION]


def save_audit_sandbox(document: dict[str, Any]) -> dict[str, Any]:
    _collection().insert_one(document)
    document.pop("_id", None)
    return document


def replace_audit_sandbox(audit_id: str, document: dict[str, Any]) -> dict[str, Any]:
    _collection().replace_one({"audit_id": audit_id}, document, upsert=True)
    document.pop("_id", None)
    return document


def get_audit_sandbox(audit_id: str) -> dict[str, Any] | None:
    doc = _collection().find_one({"audit_id": audit_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


def get_latest_audit_for_session(session_id: str) -> dict[str, Any] | None:
    doc = _collection().find_one(
        {"session_id": session_id},
        sort=[("updated_at", -1)],
    )
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_test_case_execution(
    audit_id: str,
    test_case_id: str,
    *,
    status: str | None = None,
    execution_patch: dict[str, Any],
) -> dict[str, Any] | None:
    """Read-modify-write a single test case execution nested in the audit doc."""
    doc = get_audit_sandbox(audit_id)
    if doc is None:
        return None

    cases = doc.get("test_cases") or []
    case_index = next(
        (i for i, tc in enumerate(cases) if tc.get("test_case_id") == test_case_id),
        None,
    )
    if case_index is None:
        return None

    case = dict(cases[case_index])
    execution = dict(case.get("execution") or {})
    execution.update(execution_patch)
    case["execution"] = execution
    if status is not None:
        case["status"] = status
    cases[case_index] = case
    doc["test_cases"] = cases
    doc["updated_at"] = _utc_now()
    return replace_audit_sandbox(audit_id, doc)
