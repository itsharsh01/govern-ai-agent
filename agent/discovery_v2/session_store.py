from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pymongo.collection import Collection

from agent.api.mongo.client import get_database
from agent.discovery_v2.config import discovery_collection
from agent.discovery_v2.models import SessionState
from agent.discovery_v2.state_ops import init_session_state


def _collection() -> Collection:
    return get_database()[discovery_collection()]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def create_session(self, customer_id: str | None = None) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        state = init_session_state(session_id)
        now = _now_iso()
        doc = {
            "session_id": session_id,
            "customer_id": customer_id,
            "state": state.model_dump(mode="json"),
            "conversation": [],
            "completion_outputs": None,
            "created_at": now,
            "updated_at": now,
        }
        _collection().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def load_session(self, session_id: str) -> dict[str, Any]:
        doc = _collection().find_one({"session_id": session_id})
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery session '{session_id}' not found",
            )
        doc.pop("_id", None)
        return doc

    def save_session(self, session: dict[str, Any]) -> None:
        session["updated_at"] = _now_iso()
        _collection().update_one(
            {"session_id": session["session_id"]},
            {
                "$set": {
                    "state": session["state"],
                    "conversation": session["conversation"],
                    "completion_outputs": session.get("completion_outputs"),
                    "customer_id": session.get("customer_id"),
                    "updated_at": session["updated_at"],
                }
            },
        )

    def get_state(self, session: dict[str, Any]) -> SessionState:
        return SessionState.model_validate(session["state"])

    def set_state(self, session: dict[str, Any], state: SessionState) -> None:
        session["state"] = state.model_dump(mode="json")

    def find_session_for_customer(self, customer_id: str) -> dict[str, Any] | None:
        from agent.api.mongo.repository import load_customer

        try:
            customer = load_customer(customer_id)
        except HTTPException:
            return None

        if customer.discovery_session_id:
            doc = _collection().find_one({"session_id": customer.discovery_session_id})
            if doc is not None:
                doc.pop("_id", None)
                return doc

        doc = _collection().find_one(
            {"customer_id": customer_id},
            sort=[("created_at", 1)],
        )
        if doc is None:
            return None
        doc.pop("_id", None)
        if not customer.discovery_session_id:
            from agent.api.mongo.repository import link_discovery_session

            link_discovery_session(customer_id, doc["session_id"])
        return doc
