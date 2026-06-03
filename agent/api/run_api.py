"""Start the GovernAI customer API.

    uv run python agent/api/run_api.py
"""

from dotenv import load_dotenv

load_dotenv()

from agent.api.main import run

if __name__ == "__main__":
    run()
