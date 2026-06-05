from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def normalize_system_url(url: str) -> str:
    """Ensure agent HTTP endpoints include a path (e.g. /chat on port 8820)."""
    raw = url.strip()
    if not raw:
        return raw

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return raw

    path = parsed.path.rstrip("/") or ""
    port = parsed.port

    # Portfolio example agent: POST must hit /chat
    if path in ("", "/") and port == 8820:
        path = "/chat"

    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            path if path.startswith("/") else f"/{path}",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    return normalized.rstrip("/") if path == "/chat" else normalized
