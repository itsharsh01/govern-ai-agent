from __future__ import annotations

from fastapi import APIRouter

from agent.api.schemas import (
    ApplicationType,
    Environment,
    SensitiveDataAsset,
    ToolCategory,
)

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/options")
def get_form_options() -> dict:
    """Dropdown / multi-select options for the onboarding UI."""
    return {
        "application_types": [e.value for e in ApplicationType],
        "environments": [e.value for e in Environment],
        "tool_categories": [e.value for e in ToolCategory],
        "sensitive_data_assets": [e.value for e in SensitiveDataAsset],
        "policy_types": ["governance", "privacy", "security", "compliance"],
    }
