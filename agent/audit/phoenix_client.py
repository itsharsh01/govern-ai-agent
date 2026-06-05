from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

DEFAULT_ATTEMPTS = 6
DEFAULT_PAUSE_SECONDS = 1.0
SPAN_NAME = "governai.process"


def phoenix_api_base() -> str | None:
    endpoint = (
        os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
        or os.getenv("PHOENIX_BASE_URL")
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or ""
    ).strip().rstrip("/")
    if not endpoint:
        return None
    if endpoint.endswith("/v1/traces"):
        return endpoint[: -len("/v1/traces")]
    return endpoint


def phoenix_configured() -> bool:
    return bool(os.getenv("PHOENIX_API_KEY", "").strip() and phoenix_api_base())


def _project_name() -> str:
    return os.getenv("PHOENIX_PROJECT_NAME", "governai").strip() or "governai"


def _list_recent_spans(*, since: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    api_key = os.getenv("PHOENIX_API_KEY", "").strip()
    base = phoenix_api_base()
    if not api_key or not base:
        return []

    url = f"{base}/v1/projects/{quote(_project_name(), safe='')}/spans"
    headers = {"Authorization": f"Bearer {api_key}"}
    params: list[tuple[str, str | int]] = [
        ("limit", limit),
        ("name", SPAN_NAME),
    ]
    if since:
        params.append(("start_time", since))

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers, params=params)
    except httpx.HTTPError as exc:
        logger.warning("Phoenix span list failed: %s", exc)
        return []

    if response.status_code != 200:
        logger.warning(
            "Phoenix span list HTTP %s: %s",
            response.status_code,
            response.text[:300],
        )
        return []

    payload = response.json()
    data = payload.get("data")
    return data if isinstance(data, list) else []


def _span_to_link(span: dict[str, Any]) -> dict[str, Any]:
    context = span.get("context") or {}
    return {
        "phoenix_span_global_id": span.get("id"),
        "phoenix_trace_id": context.get("trace_id"),
        "phoenix_span_id": context.get("span_id"),
        "phoenix_span_name": span.get("name"),
        "phoenix_start_time": span.get("start_time"),
        "phoenix_end_time": span.get("end_time"),
    }


def _pick_latest_span(
    spans: list[dict[str, Any]],
    *,
    exclude_trace_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    excluded = exclude_trace_ids or set()
    candidates: list[dict[str, Any]] = []
    for span in spans:
        context = span.get("context") or {}
        trace_id = context.get("trace_id")
        if trace_id and trace_id in excluded:
            continue
        candidates.append(span)

    if not candidates:
        return None

    def sort_key(span: dict[str, Any]) -> str:
        return str(span.get("end_time") or span.get("start_time") or "")

    return max(candidates, key=sort_key)


def fetch_trace_by_context(
    *,
    since: str | None = None,
    exclude_trace_ids: set[str] | None = None,
    max_attempts: int = DEFAULT_ATTEMPTS,
    pause_seconds: float = DEFAULT_PAUSE_SECONDS,
) -> dict[str, Any] | None:
    """Return the newest governai.process span from Phoenix (OTLP ingest may lag)."""
    if not phoenix_configured():
        return None

    for attempt in range(max_attempts):
        spans = _list_recent_spans(since=since, limit=10)
        latest = _pick_latest_span(spans, exclude_trace_ids=exclude_trace_ids)
        if latest is not None:
            return _span_to_link(latest)
        if attempt < max_attempts - 1:
            time.sleep(pause_seconds * (attempt + 1))

    logger.info("No recent Phoenix trace found for %s", SPAN_NAME)
    return None


def fetch_latest_trace(
    *,
    since: str | None = None,
    exclude_trace_ids: set[str] | None = None,
    max_attempts: int = DEFAULT_ATTEMPTS,
    pause_seconds: float = DEFAULT_PAUSE_SECONDS,
) -> dict[str, Any] | None:
    """Backward-compatible alias for fetch_trace_by_context."""
    return fetch_trace_by_context(
        since=since,
        exclude_trace_ids=exclude_trace_ids,
        max_attempts=max_attempts,
        pause_seconds=pause_seconds,
    )


def _list_spans_by_trace_id(trace_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    api_key = os.getenv("PHOENIX_API_KEY", "").strip()
    base = phoenix_api_base()
    if not api_key or not base:
        return []

    url = f"{base}/v1/projects/{quote(_project_name(), safe='')}/spans"
    headers = {"Authorization": f"Bearer {api_key}"}
    params: list[tuple[str, str | int]] = [
        ("limit", limit),
        ("trace_id", trace_id),
    ]

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers, params=params)
    except httpx.HTTPError as exc:
        logger.warning("Phoenix span list by trace_id failed: %s", exc)
        return []

    if response.status_code != 200:
        logger.warning(
            "Phoenix span list by trace_id HTTP %s: %s",
            response.status_code,
            response.text[:300],
        )
        return []

    payload = response.json()
    data = payload.get("data")
    return data if isinstance(data, list) else []


def _extract_trace_payload(span: dict[str, Any]) -> dict[str, Any] | None:
    attributes = span.get("attributes") or {}
    raw = attributes.get("governai.trace")
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            logger.warning("Failed to parse governai.trace attribute JSON")
            return None
    return None


def fetch_trace_payload(trace_id: str) -> dict[str, Any] | None:
    """Fetch parsed governai.trace payload for a Phoenix trace_id."""
    if not phoenix_configured() or not trace_id:
        return None

    spans = _list_spans_by_trace_id(trace_id)
    process_spans = [span for span in spans if span.get("name") == SPAN_NAME]
    candidates = process_spans or spans
    if not candidates:
        return None

    for span in candidates:
        payload = _extract_trace_payload(span)
        if payload is not None:
            return payload

    return None


def execution_started_at() -> str:
    return datetime.now(timezone.utc).isoformat()
