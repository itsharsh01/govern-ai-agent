from __future__ import annotations

from agent.discovery.interaction_resolver import resolve_interaction
from agent.discovery.models import InteractionType
from agent.discovery.schema_utils import new_session_schema


def test_resolve_multi_select_for_pii_categories():
    schema = new_session_schema("s1")
    interaction = resolve_interaction(
        schema,
        "data_assets.pii_categories",
        "What PII can the system access?",
    )
    assert interaction is not None
    assert interaction.type == InteractionType.MULTI_SELECT
    assert len(interaction.options) > 0


def test_resolve_document_upload_for_policy_refs():
    schema = new_session_schema("s1")
    interaction = resolve_interaction(
        schema,
        "policies.policy_document_refs",
        "Please upload policies.",
    )
    assert interaction is not None
    assert interaction.type == InteractionType.DOCUMENT_UPLOAD


def test_resolve_multi_input_for_api_list():
    schema = new_session_schema("s1")
    interaction = resolve_interaction(
        schema,
        "tooling.apis.api_list",
        "Which APIs are connected?",
    )
    assert interaction is not None
    assert interaction.type == InteractionType.MULTI_INPUT


def test_resolve_text_for_business_purpose():
    schema = new_session_schema("s1")
    interaction = resolve_interaction(
        schema,
        "system_profile.business_purpose",
        "What is the business purpose?",
    )
    assert interaction is not None
    assert interaction.type == InteractionType.TEXT
