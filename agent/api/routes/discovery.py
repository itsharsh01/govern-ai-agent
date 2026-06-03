from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from agent.api.discovery_schemas import (
    CreateDiscoverySessionRequest,
    DigitalTwinResponse,
    DiscoveryProgressResponse,
    DiscoverySessionResponse,
    PostDiscoveryMessageRequest,
)
from agent.api.storage import discovery_uploads_dir, ensure_dirs
from agent.discovery.models import DiscoveryTurnResponse, StructuredInteractionPayload
from agent.discovery.orchestrator import create_session, process_structured_turn, process_turn
from agent.discovery.repository import DiscoveryRepository

router = APIRouter(prefix="/discovery", tags=["discovery"])
_repository = DiscoveryRepository()

ALLOWED_DOC_EXTENSIONS = {".pdf", ".json", ".yaml", ".yml"}


@router.post("/sessions", response_model=DiscoveryTurnResponse, status_code=status.HTTP_201_CREATED)
def start_discovery_session(body: CreateDiscoverySessionRequest) -> DiscoveryTurnResponse:
    return create_session(customer_id=body.customer_id)


@router.post("/sessions/{session_id}/messages", response_model=DiscoveryTurnResponse)
def post_discovery_message(session_id: str, body: PostDiscoveryMessageRequest) -> DiscoveryTurnResponse:
    if body.interaction:
        payload = StructuredInteractionPayload.model_validate(body.interaction)
        return process_structured_turn(session_id, payload)
    if body.message and body.message.strip():
        return process_turn(session_id, body.message.strip())
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Provide either message or interaction",
    )


@router.post("/sessions/{session_id}/documents", response_model=DiscoveryTurnResponse)
async def upload_discovery_documents(
    session_id: str,
    field_path: str = Form(...),
    files: list[UploadFile] = File(...),
) -> DiscoveryTurnResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No files provided")

    ensure_dirs()
    upload_dir = discovery_uploads_dir(session_id)
    saved_names: list[str] = []

    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in ALLOWED_DOC_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(sorted(ALLOWED_DOC_EXTENSIONS))}",
            )
        safe_name = Path(upload.filename or "document").name
        dest = upload_dir / safe_name
        content = await upload.read()
        dest.write_bytes(content)
        saved_names.append(safe_name)

    payload = StructuredInteractionPayload(
        type="document_upload",
        field_path=field_path,
        files=saved_names,
    )
    return process_structured_turn(session_id, payload)


@router.get("/sessions/{session_id}", response_model=DiscoverySessionResponse)
def get_discovery_session(session_id: str) -> DiscoverySessionResponse:
    session = _repository.load_session(session_id)
    schema = session["schema"]
    return DiscoverySessionResponse(
        session_id=session["session_id"],
        customer_id=session.get("customer_id"),
        discovery_schema=schema,
        conversation=session.get("conversation", []),
        discovery_complete=schema["discovery_state"]["discovery_complete"],
    )


@router.get("/sessions/{session_id}/progress", response_model=DiscoveryProgressResponse)
def get_discovery_progress(session_id: str) -> DiscoveryProgressResponse:
    session = _repository.load_session(session_id)
    state = session["schema"]["discovery_state"]
    return DiscoveryProgressResponse(
        session_id=session["session_id"],
        overall_completeness=state["overall_completeness"],
        overall_confidence=state["overall_confidence"],
        discovery_phase=state["discovery_phase"]["value"],
        section_progress=state["section_progress"],
        conversation_turns=state["conversation_turns"],
        discovery_complete=state["discovery_complete"],
        remaining_gaps=state.get("critical_gaps") or [],
    )


@router.get("/sessions/{session_id}/digital-twin", response_model=DigitalTwinResponse)
def get_digital_twin(session_id: str) -> DigitalTwinResponse:
    session = _repository.load_session(session_id)
    schema = session["schema"]
    if not schema["discovery_state"]["discovery_complete"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery is not complete for this session",
        )

    outputs = session.get("completion_outputs")
    if outputs is None:
        from agent.discovery.digital_twin import DigitalTwinGenerator

        outputs = DigitalTwinGenerator().generate(schema).model_dump(mode="json")
        _repository.save_completion_outputs(session_id, outputs)

    return DigitalTwinResponse(
        session_id=session_id,
        system_summary=outputs["system_summary"],
        digital_twin=outputs["digital_twin"],
        discovered_risks=outputs["discovered_risks"],
        governance_readiness_report=outputs["governance_readiness_report"],
        kg_mappings=outputs.get("kg_mappings") or [],
    )
