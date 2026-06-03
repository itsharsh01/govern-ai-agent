from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GapKind(StrEnum):
    MISSING = "missing"
    INFERRED_UNVALIDATED = "inferred_unvalidated"
    LOW_CONFIDENCE = "low_confidence"


class InteractionType(StrEnum):
    TEXT = "text"
    MULTI_SELECT = "multi_select"
    MULTI_INPUT = "multi_input"
    DOCUMENT_UPLOAD = "document_upload"


class InteractionOption(BaseModel):
    id: str
    label: str
    description: str = ""


class InteractionRequest(BaseModel):
    type: InteractionType
    field_path: str
    prompt: str
    options: list[InteractionOption] = Field(default_factory=list)
    min_selections: int = 0
    max_selections: int | None = None
    input_label: str | None = None
    input_placeholder: str | None = None
    key_label: str | None = None
    accept: str | None = None
    max_files: int = 5


class StructuredInteractionPayload(BaseModel):
    type: InteractionType
    field_path: str
    values: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)


class ExtractedFact(BaseModel):
    type: str
    field_path: str | None = None
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    source_message: str | None = None


class FactExtractionResult(BaseModel):
    facts: list[ExtractedFact] = Field(default_factory=list)


class SchemaGap(BaseModel):
    field_path: str
    section: str
    kind: GapKind
    required: bool
    priority: str = "medium"
    current_confidence: float = 0.0
    rationale: str


class RankedGap(BaseModel):
    field_path: str
    section: str
    risk_score: float
    kind: GapKind
    rationale: str


class DiscoveryProgress(BaseModel):
    overall_completeness: float
    overall_confidence: float
    discovery_phase: str
    section_progress: dict[str, Any]
    conversation_turns: int


class DiscoveryTurnResponse(BaseModel):
    session_id: str
    assistant_message: str
    discovery_progress: DiscoveryProgress
    current_understanding: list[str]
    remaining_gaps: list[RankedGap]
    discovery_complete: bool
    completion_outputs: dict[str, Any] | None = None
    interaction: InteractionRequest | None = None


class DigitalTwinOutput(BaseModel):
    system_summary: str
    digital_twin: dict[str, Any]
    discovered_risks: list[dict[str, Any]]
    governance_readiness_report: dict[str, Any]
    kg_mappings: list[dict[str, Any]] = Field(default_factory=list)
