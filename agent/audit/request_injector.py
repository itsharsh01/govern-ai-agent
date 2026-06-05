from __future__ import annotations

import copy
import json
from typing import Any

PROMPT_KEYS = ("query", "message", "input", "prompt", "user_message", "text")


def _body_as_dict(sample_request_body: dict[str, Any] | str | None) -> dict[str, Any]:
    if isinstance(sample_request_body, dict):
        return copy.deepcopy(sample_request_body)
    if isinstance(sample_request_body, str):
        trimmed = sample_request_body.strip()
        if trimmed:
            try:
                parsed = json.loads(trimmed)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
    return {}


def inject_user_prompt(
    sample_request_body: dict[str, Any] | str | None,
    user_prompt: str,
) -> dict[str, Any] | str:
    body = _body_as_dict(sample_request_body)

    for key in PROMPT_KEYS:
        if key in body:
            body[key] = user_prompt
            return body

    body["query"] = user_prompt
    return body
