"""Debug helper: list recent Phoenix spans."""

from __future__ import annotations

import os
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    base = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "").rstrip("/")
    key = os.getenv("PHOENIX_API_KEY", "")
    proj = os.getenv("PHOENIX_PROJECT_NAME", "")
    url = f"{base}/v1/projects/{quote(proj, safe='')}/spans"
    headers = {"Authorization": f"Bearer {key}"}

    for params in [{"limit": 10}, {"limit": 10, "name": "governai.process"}]:
        r = httpx.get(url, headers=headers, params=params, timeout=30)
        print("params", params, "status", r.status_code)
        data = r.json().get("data") or []
        print("count", len(data))
        for span in data[:5]:
            ctx = span.get("context") or {}
            print(" -", span.get("name"), ctx.get("trace_id"), span.get("start_time"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
