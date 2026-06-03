from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class CreateDiscoverySessionRequest(BaseModel):
    customer_id: str | None = None


class PostDiscoveryMessageRequest(BaseModel):
    message: str | None = None
    interaction: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_message_or_interaction(self) -> PostDiscoveryMessageRequest:
        has_message = bool(self.message and self.message.strip())
        has_interaction = self.interaction is not None
        if not has_message and not has_interaction:
            raise ValueError("Provide either message or interaction")
        return self


class DiscoverySessionResponse(BaseModel):
    session_id: str
    customer_id: str | None = None
    discovery_schema: dict[str, Any]
    conversation: list[dict[str, Any]]
    discovery_complete: bool


class DiscoveryProgressResponse(BaseModel):
    session_id: str
    overall_completeness: float
    overall_confidence: float
    discovery_phase: str
    section_progress: dict[str, Any]
    conversation_turns: int
    discovery_complete: bool
    remaining_gaps: list[dict[str, Any]]


class DigitalTwinResponse(BaseModel):
    session_id: str
    system_summary: str
    digital_twin: dict[str, Any]
    discovered_risks: list[dict[str, Any]]
    governance_readiness_report: dict[str, Any]
    kg_mappings: list[dict[str, Any]]
