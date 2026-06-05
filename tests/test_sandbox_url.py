from __future__ import annotations

from agent.audit.request_injector import inject_user_prompt
from agent.audit.sandbox_url import normalize_system_url


def test_normalize_appends_chat_for_port_8820():
    assert normalize_system_url("http://127.0.0.1:8820") == "http://127.0.0.1:8820/chat"
    assert normalize_system_url("http://127.0.0.1:8820/") == "http://127.0.0.1:8820/chat"


def test_normalize_keeps_existing_path():
    assert (
        normalize_system_url("http://127.0.0.1:8820/chat")
        == "http://127.0.0.1:8820/chat"
    )


def test_inject_parses_json_string_body():
    body = '{"query": "old"}'
    result = inject_user_prompt(body, "new prompt")
    assert result == {"query": "new prompt"}
