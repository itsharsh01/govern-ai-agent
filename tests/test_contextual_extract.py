from __future__ import annotations

from agent.discovery.fact_extractor import FactExtractionEngine
from agent.discovery.schema_utils import new_session_schema


def test_yes_maps_to_last_asked_field():
    schema = new_session_schema("s1")
    schema["discovery_state"]["next_question_context"] = {
        "target_field": "data_assets.sensitive_financial_data",
        "target_section": "data_assets",
        "question_text": "Does the system process sensitive financial data?",
    }
    facts = FactExtractionEngine().extract(schema, "yes")
    assert len(facts) >= 1
    assert facts[0].field_path == "data_assets.sensitive_financial_data"
    assert facts[0].value is True
    assert facts[0].confidence >= 0.9


def test_no_maps_to_last_asked_field():
    schema = new_session_schema("s1")
    schema["discovery_state"]["next_question_context"] = {
        "target_field": "data_assets.sensitive_financial_data",
        "target_section": "data_assets",
        "question_text": "Does the system process sensitive financial data?",
    }
    facts = FactExtractionEngine().extract(schema, "no")
    assert facts[0].value is False


def test_yes_advances_state_and_does_not_repeat_same_gap():
    from agent.discovery.gap_analyzer import GapAnalysisEngine
    from agent.discovery.question_generator import QuestionGenerationEngine
    from agent.discovery.risk_prioritizer import RiskPrioritizationEngine
    from agent.discovery.state_manager import DiscoveryStateManager

    schema = new_session_schema("s1")
    schema["discovery_state"]["next_question_context"] = {
        "target_field": "data_assets.sensitive_financial_data",
        "target_section": "data_assets",
        "question_text": "Does the system process sensitive financial data?",
    }
    schema["discovery_state"]["conversation_turns"] = 2

    facts = FactExtractionEngine().extract(schema, "yes")
    DiscoveryStateManager().apply_facts(schema, facts, "yes")

    gaps = GapAnalysisEngine().analyze(schema)
    ranked = RiskPrioritizationEngine().prioritize(schema, gaps)
    target = QuestionGenerationEngine().select_target(ranked, 2, schema)

    assert target is not None
    assert target.field_path != "data_assets.sensitive_financial_data"
