from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.audit.sandbox_probe import probe_sandbox


@patch("agent.audit.sandbox_probe.httpx.Client")
def test_probe_sandbox_passes_on_200(mock_client_cls):
    response = MagicMock()
    response.status_code = 200
    response.text = '{"answer":"ok"}'

    client = MagicMock()
    client.__enter__.return_value = client
    client.post.return_value = response
    mock_client_cls.return_value = client

    result = probe_sandbox(
        system_url="http://127.0.0.1:8820/chat",
        sample_request_body={"query": "hello"},
    )

    assert result["passed"] is True
    assert result["status_code"] == 200


@patch("agent.audit.sandbox_probe.httpx.Client")
def test_probe_sandbox_fails_on_non_200(mock_client_cls):
    response = MagicMock()
    response.status_code = 500
    response.text = "error"

    client = MagicMock()
    client.__enter__.return_value = client
    client.post.return_value = response
    mock_client_cls.return_value = client

    result = probe_sandbox(
        system_url="http://127.0.0.1:8820/chat",
        sample_request_body={"query": "hello"},
    )

    assert result["passed"] is False
    assert result["status_code"] == 500
