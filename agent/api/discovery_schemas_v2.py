from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agent.discovery_v2.models import TurnResponse, UIHint


class CreateSessionRequest(BaseModel):
    customer_id: str | None = None


class TurnRequest(BaseModel):
    message: str | None = None
    answers: dict[str, Any] | None = Field(
        default=None,
        description="Structured answers keyed by schema dot-path",
    )


class SessionSummaryResponse(BaseModel):
    session_id: str
    customer_id: str | None = None
    conversation: list[dict[str, str]] = Field(default_factory=list)
    completion_pct: float = 0.0
    remaining_keys: int = 0
    discovery_complete: bool = False
    current_key: str | None = None
    high_risk_flags_triggered: list[str] = Field(default_factory=list)
    discovered_count: int = 0


class CompletionResponse(BaseModel):
    session_id: str
    system_summary: str
    discovered: dict[str, Any]
    discovered_risks: list[dict[str, Any]]
    governance_readiness_report: dict[str, Any]
