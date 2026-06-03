from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from agent.api.discovery_schemas_v2 import (
    CompletionResponse,
    CreateSessionRequest,
    SessionSummaryResponse,
    TurnRequest,
)
from agent.discovery_v2.boot import create_session, iter_boot_events
from agent.discovery_v2.models import TurnResponse
from agent.discovery_v2.session_store import SessionStore
from agent.discovery_v2.turn_runner import iter_turn_events, run_turn

router = APIRouter(prefix="/discovery", tags=["discovery-v2"])
_store = SessionStore()


@router.post("/sessions", response_model=TurnResponse, status_code=status.HTTP_201_CREATED)
def start_session(body: CreateSessionRequest) -> TurnResponse:
    return create_session(customer_id=body.customer_id)


@router.post("/sessions/stream")
def start_session_stream(body: CreateSessionRequest) -> StreamingResponse:
    def events():
        for event in iter_boot_events(customer_id=body.customer_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/turns", response_model=TurnResponse)
def post_turn(session_id: str, body: TurnRequest) -> TurnResponse:
    if not body.message and not body.answers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide message or answers",
        )
    return run_turn(session_id, message=body.message, answers=body.answers)


@router.post("/sessions/{session_id}/turns/stream")
def post_turn_stream(session_id: str, body: TurnRequest) -> StreamingResponse:
    if not body.message and not body.answers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide message or answers",
        )

    def events():
        for event in iter_turn_events(
            session_id, message=body.message, answers=body.answers
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/sessions/{session_id}", response_model=SessionSummaryResponse)
def get_session(session_id: str) -> SessionSummaryResponse:
    session = _store.load_session(session_id)
    state = _store.get_state(session)
    return SessionSummaryResponse(
        session_id=session_id,
        customer_id=session.get("customer_id"),
        conversation=session.get("conversation", []),
        completion_pct=state.completion_pct,
        remaining_keys=state.remaining_keys,
        discovery_complete=state.discovery_complete,
        current_key=state.current_key,
        high_risk_flags_triggered=state.high_risk_flags_triggered,
        discovered_count=len(state.discovered),
    )


@router.get("/sessions/{session_id}/completion", response_model=CompletionResponse)
def get_completion(session_id: str) -> CompletionResponse:
    session = _store.load_session(session_id)
    state = _store.get_state(session)
    if not state.discovery_complete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery is not complete for this session",
        )
    outputs = session.get("completion_outputs")
    if not outputs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Completion outputs not generated",
        )
    return CompletionResponse(
        session_id=session_id,
        system_summary=outputs["system_summary"],
        discovered=outputs["discovered"],
        discovered_risks=outputs["discovered_risks"],
        governance_readiness_report=outputs["governance_readiness_report"],
    )
