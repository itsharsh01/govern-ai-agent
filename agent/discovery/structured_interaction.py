from __future__ import annotations

from typing import Any

from agent.discovery.models import ExtractedFact, InteractionType, StructuredInteractionPayload


def structured_to_message(payload: StructuredInteractionPayload) -> str:
    if payload.type == InteractionType.MULTI_SELECT:
        items = ", ".join(payload.values)
        return f"Selected for {payload.field_path}: {items}"
    if payload.type == InteractionType.MULTI_INPUT:
        items = "; ".join(payload.values)
        return f"Provided for {payload.field_path}: {items}"
    if payload.type == InteractionType.DOCUMENT_UPLOAD:
        files = ", ".join(payload.files)
        return f"Uploaded documents for {payload.field_path}: {files}"
    return payload.values[0] if payload.values else ""


def structured_to_facts(payload: StructuredInteractionPayload) -> list[ExtractedFact]:
    message = structured_to_message(payload)
    if payload.type == InteractionType.MULTI_SELECT:
        value: Any = payload.values[0] if len(payload.values) == 1 else payload.values
        return [
            ExtractedFact(
                type="structured",
                field_path=payload.field_path,
                value=value,
                confidence=0.95,
                source_message=message,
            )
        ]
    if payload.type == InteractionType.MULTI_INPUT:
        return [
            ExtractedFact(
                type="structured",
                field_path=payload.field_path,
                value=payload.values,
                confidence=0.95,
                source_message=message,
            )
        ]
    if payload.type == InteractionType.DOCUMENT_UPLOAD:
        return [
            ExtractedFact(
                type="structured",
                field_path=payload.field_path,
                value=payload.files,
                confidence=0.95,
                source_message=message,
            )
        ]
    return []
