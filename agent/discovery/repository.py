from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pymongo.collection import Collection

from agent.api.mongo.client import get_database
from agent.discovery.schema_utils import new_session_schema

DISCOVERY_COLLECTION = os.getenv("MONGO_DISCOVERY_COLLECTION", "discovery_sessions")


def _collection() -> Collection:
    return get_database()[DISCOVERY_COLLECTION]


class DiscoveryRepository:
    def create_session(self, customer_id: str | None = None) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        session = {
            "session_id": session_id,
            "customer_id": customer_id,
            "schema": new_session_schema(session_id),
            "conversation": [],
            "completion_outputs": None,
            "created_at": now,
            "updated_at": now,
        }
        _collection().insert_one(session)
        session.pop("_id", None)
        return session

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
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        _collection().replace_one({"session_id": session["session_id"]}, session, upsert=True)

    def save_completion_outputs(self, session_id: str, outputs: dict[str, Any]) -> None:
        _collection().update_one(
            {"session_id": session_id},
            {"$set": {"completion_outputs": outputs, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
