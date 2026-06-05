from __future__ import annotations

import json
from typing import Any

import httpx

from agent.audit.sandbox_url import normalize_system_url

DEFAULT_TIMEOUT_SECONDS = 90.0


def _format_error_detail(status_code: int, text: str | None) -> str:
    if not text:
        return f"Sandbox returned HTTP {status_code}; expected 200."
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if detail:
                if isinstance(detail, list):
                    detail = json.dumps(detail)
                return f"Sandbox returned HTTP {status_code}: {detail}"
    except json.JSONDecodeError:
        pass
    preview = text[:500] + ("..." if len(text) > 500 else "")
    return f"Sandbox returned HTTP {status_code}; expected 200. Body: {preview}"


def probe_sandbox(
    *,
    system_url: str,
    auth_token: str | None = None,
    sample_request_body: dict[str, Any] | str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """POST to the client system URL and require HTTP 200."""
    url = normalize_system_url(system_url)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = (auth_token or "").strip()
    if token:
        headers["Authorization"] = token if token.lower().startswith("bearer ") else f"Bearer {token}"
    if isinstance(sample_request_body, str):
        trimmed = sample_request_body.strip()
        if trimmed:
            try:
                json_body = json.loads(trimmed)
                if not isinstance(json_body, dict):
                    json_body = None
                    content = trimmed
                else:
                    content = None
            except json.JSONDecodeError:
                json_body = None
                content = trimmed
        else:
            json_body = {}
            content = None
    elif sample_request_body is not None:
        json_body = sample_request_body
        content = None
    else:
        json_body = {}
        content = None

    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.post(url, json=json_body, content=content, headers=headers)
    except httpx.HTTPError as exc:
        return {
            "passed": False,
            "status_code": 0,
            "response_preview": None,
            "message": f"Connection failed: {exc}",
            "request_url": url,
        }

    preview: str | None = None
    try:
        text = response.text
        preview = text[:2000] if text else None
    except Exception:
        preview = None

    passed = response.status_code == 200
    if passed:
        message = "Sandbox connection OK (HTTP 200)."
    else:
        message = _format_error_detail(response.status_code, response.text)

    return {
        "passed": passed,
        "status_code": response.status_code,
        "response_preview": preview,
        "message": message,
        "request_url": url,
    }
