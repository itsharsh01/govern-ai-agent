"""Load govern-ai-agent/.env regardless of process working directory."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# govern-ai-agent/ (parent of agent/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def load_project_env() -> Path:
    """Load .env from project root; .env values override existing shell env."""
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE, override=True)
    return ENV_FILE
