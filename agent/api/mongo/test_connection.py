"""Test MongoDB connection.

    uv run python agent/api/mongo/test_connection.py
"""

from dotenv import load_dotenv

from agent.api.mongo import close_mongo, connect_mongo, verify_connection


def main() -> int:
    load_dotenv()
    try:
        connect_mongo()
        info = verify_connection()
        print("MongoDB connection OK")
        for key, value in info.items():
            print(f"  {key}: {value}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        close_mongo()


if __name__ == "__main__":
    raise SystemExit(main())
