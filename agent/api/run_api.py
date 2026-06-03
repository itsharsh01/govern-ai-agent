"""Start the GovernAI customer API.

    uv run python agent/api/run_api.py
"""

from agent.api._env import load_project_env

load_project_env()

from agent.api.main import run

if __name__ == "__main__":
    run()
