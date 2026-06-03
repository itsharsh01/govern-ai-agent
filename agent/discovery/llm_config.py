from __future__ import annotations

import os


def discovery_llm_enabled() -> bool:
    if os.getenv("DISCOVERY_DISABLE_LLM", "").lower() in {"1", "true", "yes"}:
        return False
    return bool(os.getenv("GOOGLE_API_KEY", "").strip())
