from __future__ import annotations

import pytest

from agent.discovery.fact_extractor import _rule_based_extract


def test_rule_based_extract_finds_tools_and_framework():
    message = "We built a banking support assistant using LangGraph. It connects to our CRM and KYC API."
    facts = _rule_based_extract(message)
    types = {fact.type for fact in facts}
    assert "tool" in types
    assert "framework" in types
    tool_facts = [f for f in facts if f.type == "tool"]
    tool_values = {str(f.value).upper() for f in tool_facts}
    assert "CRM" in tool_values


def test_rule_based_extract_detects_rag():
    facts = _rule_based_extract("The assistant uses RAG over internal policy documents.")
    assert any(f.field_path == "knowledge_sources.uses_rag" for f in facts)
