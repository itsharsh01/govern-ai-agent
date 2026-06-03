from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Iterator
from typing import Any

from agent.discovery_v2.config import discovery_llm_models, groq_api_key, llm_enabled

logger = logging.getLogger(__name__)

_llm_degraded = False
_rate_cooldown_until = 0.0
_last_rate_log_at = 0.0

_RATE_MARKERS = (
    "rate limit",
    "rate_limit",
    "quota",
    "429",
    "too many requests",
)
_TRANSIENT_MARKERS = (
    "overloaded",
    "unavailable",
    "503",
    "502",
    "500",
    "try again",
)


def reset_llm_status() -> None:
    global _llm_degraded, _rate_cooldown_until, _last_rate_log_at
    _llm_degraded = False
    _rate_cooldown_until = 0.0
    _last_rate_log_at = 0.0


def llm_was_degraded() -> bool:
    return _llm_degraded


def llm_in_cooldown() -> bool:
    return time.time() < _rate_cooldown_until


def discovery_llm_available() -> bool:
    return llm_enabled() and not llm_in_cooldown()


def _mark_llm_ok() -> None:
    global _llm_degraded
    _llm_degraded = False


def _mark_llm_degraded() -> None:
    global _llm_degraded
    _llm_degraded = True


def _short_error(exc: BaseException) -> str:
    text = str(exc).replace("\n", " ")
    return text[:240] + ("..." if len(text) > 240 else "")


def _extract_retry_seconds(exc: BaseException) -> float:
    match = re.search(r"retry (?:in |after )?(\d+(?:\.\d+)?)\s*s", str(exc), re.I)
    if match:
        return min(max(float(match.group(1)), 5.0), 300.0)
    return 30.0


def _is_rate_limited(exc: BaseException) -> bool:
    try:
        from groq import RateLimitError

        if isinstance(exc, RateLimitError):
            return True
    except ImportError:
        pass
    text = str(exc).lower()
    return any(marker in text for marker in _RATE_MARKERS)


def _is_transient(exc: BaseException) -> bool:
    if _is_rate_limited(exc):
        return False
    text = str(exc).lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def _enter_rate_cooldown(exc: BaseException) -> None:
    global _rate_cooldown_until, _last_rate_log_at

    delay = _extract_retry_seconds(exc)
    _rate_cooldown_until = time.time() + delay
    _mark_llm_degraded()

    now = time.time()
    if now - _last_rate_log_at >= 30.0:
        logger.warning(
            "Discovery LLM (Groq) rate limited — pausing calls for %.0fs (%s)",
            delay,
            _short_error(exc),
        )
        _last_rate_log_at = now


def _handle_failure(exc: BaseException, model: str) -> str:
    if _is_rate_limited(exc):
        _enter_rate_cooldown(exc)
        return "abort"
    if not _is_transient(exc):
        return "raise"
    logger.debug("Discovery LLM (Groq) %s failed (%s), trying next model", model, _short_error(exc))
    time.sleep(0.3)
    return "retry"


def _client():
    from groq import Groq

    return Groq(api_key=groq_api_key())


def _messages(prompt: str, system: str | None) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def _generate_one(model: str, prompt: str, system: str | None) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=model,
        messages=_messages(prompt, system),
        temperature=0.3,
        max_tokens=512,
    )
    choice = response.choices[0] if response.choices else None
    return (choice.message.content or "").strip() if choice and choice.message else ""


def _stream_one(model: str, prompt: str, system: str | None) -> Iterator[str]:
    client = _client()
    stream = client.chat.completions.create(
        model=model,
        messages=_messages(prompt, system),
        temperature=0.3,
        max_tokens=512,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def generate_text(prompt: str, system: str | None = None) -> str:
    if not discovery_llm_available():
        if llm_enabled() and llm_in_cooldown():
            _mark_llm_degraded()
        return ""

    last_error: BaseException | None = None
    for model in discovery_llm_models():
        try:
            text = _generate_one(model, prompt, system)
            if text:
                _mark_llm_ok()
                return text
        except Exception as exc:
            last_error = exc
            action = _handle_failure(exc, model)
            if action == "abort":
                break
            if action == "raise":
                raise

    if last_error and not llm_in_cooldown():
        logger.error("All discovery LLM (Groq) models failed: %s", _short_error(last_error))
    _mark_llm_degraded()
    return ""


def stream_generate_text(prompt: str, system: str | None = None) -> Iterator[str]:
    """Yield text chunks from Groq streaming API with model fallback."""
    if not discovery_llm_available():
        if llm_enabled() and llm_in_cooldown():
            _mark_llm_degraded()
        return

    last_error: BaseException | None = None
    for model in discovery_llm_models():
        try:
            yielded = False
            for chunk in _stream_one(model, prompt, system):
                yielded = True
                yield chunk
            if yielded:
                _mark_llm_ok()
                return
            logger.debug("Discovery LLM (Groq) %s returned an empty stream", model)
            break
        except Exception as exc:
            last_error = exc
            action = _handle_failure(exc, model)
            if action == "abort":
                break
            if action == "raise":
                raise

    if last_error and not llm_in_cooldown():
        logger.error("All discovery LLM (Groq) stream models failed: %s", _short_error(last_error))
    _mark_llm_degraded()


def generate_json(prompt: str, system: str | None = None) -> dict[str, Any]:
    text = generate_text(prompt + "\n\nRespond with valid JSON only.", system=system)
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}
