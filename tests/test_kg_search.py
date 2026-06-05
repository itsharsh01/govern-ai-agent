from __future__ import annotations

from agent.vector_database.search import normalize_name


def test_normalize_name():
    assert normalize_name("  CRM Tool! ") == "crm tool"
    assert normalize_name("Customer Email") == "customer email"
