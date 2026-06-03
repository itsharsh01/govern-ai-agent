from __future__ import annotations

import copy

import pytest

from agent.discovery.gap_analyzer import GapAnalysisEngine, _should_skip_field
from agent.discovery.models import ExtractedFact, GapKind
from agent.discovery.risk_prioritizer import RiskPrioritizationEngine
from agent.discovery.schema_utils import new_session_schema
from agent.discovery.state_manager import DiscoveryStateManager


@pytest.fixture
def blank_schema():
    return new_session_schema("test-session")


def test_gap_analyzer_skips_tool_flow_when_not_agentic(blank_schema):
    assert _should_skip_field(blank_schema, "architecture.data_flow.tool_execution_flow") is True
    blank_schema["architecture"]["agentic"]["is_agentic"]["value"] = True
    blank_schema["architecture"]["agentic"]["is_agentic"]["confidence"] = 0.9
    assert _should_skip_field(blank_schema, "architecture.data_flow.tool_execution_flow") is False


def test_gap_analyzer_skips_rag_fields_when_not_rag(blank_schema):
    assert _should_skip_field(blank_schema, "knowledge_sources.knowledge_base_description") is True
    blank_schema["knowledge_sources"]["uses_rag"]["value"] = True
    blank_schema["knowledge_sources"]["uses_rag"]["confidence"] = 0.9
    assert _should_skip_field(blank_schema, "knowledge_sources.knowledge_base_description") is False


def test_gap_analyzer_finds_missing_required_fields(blank_schema):
    gaps = GapAnalysisEngine().analyze(blank_schema)
    kinds = {gap.kind for gap in gaps}
    assert GapKind.MISSING in kinds
    paths = {gap.field_path for gap in gaps}
    assert "system_profile.business_purpose" in paths


def test_state_manager_applies_tool_facts(blank_schema):
    manager = DiscoveryStateManager()
    facts = [
        ExtractedFact(
            type="tool",
            field_path="tooling.tools",
            value="CRM",
            confidence=0.95,
            source_message="We use CRM",
        )
    ]
    applied = manager.apply_facts(blank_schema, facts, "We use CRM")
    assert len(applied) == 1
    tools = blank_schema["tooling"]["tools"]
    assert any(t.get("tool_name") == "CRM" for t in tools)
    assert blank_schema["discovery_state"]["facts_extracted_total"] == 1


def test_state_manager_detects_contradiction(blank_schema):
    manager = DiscoveryStateManager()
    field = blank_schema["system_profile"]["industry"]
    field["value"] = "banking"
    field["confidence"] = 0.95
    field["source"] = "earlier"

    facts = [
        ExtractedFact(
            type="industry",
            field_path="system_profile.industry",
            value="insurance",
            confidence=0.9,
            source_message="We are in insurance",
        )
    ]
    manager.apply_facts(blank_schema, facts, "We are in insurance")
    contradictions = blank_schema["discovery_state"]["information_sources"]["contradictions_detected"]
    assert len(contradictions) == 1
    assert field["confidence"] < 0.95


def test_risk_prioritizer_ranks_data_assets_above_system_profile(blank_schema):
    gaps = GapAnalysisEngine().analyze(blank_schema)
    ranked = RiskPrioritizationEngine().prioritize(blank_schema, gaps)
    data_rank = next(i for i, g in enumerate(ranked) if g.section == "data_assets")
    profile_rank = next(i for i, g in enumerate(ranked) if g.section == "system_profile")
    assert data_rank < profile_rank


def test_state_manager_recompute_scores(blank_schema):
    manager = DiscoveryStateManager()
    blank_schema["system_profile"]["business_purpose"]["value"] = "Support banking customers"
    blank_schema["system_profile"]["business_purpose"]["confidence"] = 0.9
    blank_schema["system_profile"]["business_purpose"]["source"] = "user"
    manager.recompute_scores(blank_schema)
    assert blank_schema["discovery_state"]["overall_completeness"] > 0
    assert blank_schema["discovery_state"]["section_progress"]["system_profile"]["completeness"] > 0
