import os

import pytest


@pytest.fixture(autouse=True)
def disable_discovery_llm(monkeypatch):
    monkeypatch.setenv("DISCOVERY_DISABLE_LLM", "1")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
