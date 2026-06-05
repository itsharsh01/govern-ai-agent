from __future__ import annotations

from unittest.mock import patch

from agent.audit.phoenix_client import fetch_latest_trace, fetch_trace_payload, phoenix_api_base


def test_phoenix_api_base_strips_traces_suffix():
    with patch.dict(
        "os.environ",
        {"PHOENIX_COLLECTOR_ENDPOINT": "https://app.phoenix.arize.com/s/space/v1/traces"},
        clear=False,
    ):
        assert phoenix_api_base() == "https://app.phoenix.arize.com/s/space"


@patch("agent.audit.phoenix_client.phoenix_configured", return_value=True)
@patch("agent.audit.phoenix_client._list_recent_spans")
def test_fetch_latest_trace_picks_newest_and_skips_linked(mock_list, _mock_configured):
    mock_list.return_value = [
        {
            "id": "old",
            "name": "governai.process",
            "context": {"trace_id": "trace-old", "span_id": "span-old"},
            "end_time": "2026-06-05T10:00:00Z",
        },
        {
            "id": "new",
            "name": "governai.process",
            "context": {"trace_id": "trace-new", "span_id": "span-new"},
            "end_time": "2026-06-05T10:00:02Z",
        },
    ]

    link = fetch_latest_trace(
        exclude_trace_ids={"trace-old"},
        max_attempts=1,
        pause_seconds=0,
    )

    assert link is not None
    assert link["phoenix_trace_id"] == "trace-new"
    assert link["phoenix_span_global_id"] == "new"


@patch("agent.audit.phoenix_client.phoenix_configured", return_value=True)
@patch("agent.audit.phoenix_client._list_spans_by_trace_id")
def test_fetch_trace_payload_parses_governai_trace(mock_list, _mock_configured):
    mock_list.return_value = [
        {
            "name": "governai.process",
            "attributes": {
                "governai.trace": '{"trace_id":"t1","steps":[{"type":"tool_call","tool":"crm"}]}',
            },
        }
    ]

    payload = fetch_trace_payload("trace-abc")

    assert payload is not None
    assert payload["trace_id"] == "t1"
    assert payload["steps"][0]["tool"] == "crm"
