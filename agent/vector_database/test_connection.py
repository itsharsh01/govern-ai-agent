"""Test Qdrant connection using QDRANT_URL and QDRANT_API_KEY from .env.

    uv run python agent/vector_database/test_connection.py
"""

from dotenv import load_dotenv

from agent.vector_database import QdrantSettings, verify_connection


def main() -> int:
    load_dotenv()
    settings = QdrantSettings.from_env()
    info = verify_connection(settings)
    print("Qdrant connection OK")
    print(f"  URL:        {info['url']}")
    print(f"  Collection: {settings.collection_name}")
    print(f"  Collections: {info['collections'] or '(none yet)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
