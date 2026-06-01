"""Load the governance ontology into Neo4j.

Run whenever you want to (re)create the graph:

    uv run python agent/knowledge_graph/load_graph.py

Options:
    uv run python agent/knowledge_graph/load_graph.py --no-wipe
    uv run python agent/knowledge_graph/load_graph.py --verify

View in browser (after load):
    uv run python agent/knowledge_graph/export_graph.py
    cd agent/knowledge_graph && python -m http.server 8080
    Open http://localhost:8080/view_graph.html
"""

from dotenv import load_dotenv

from agent.knowledge_graph.loader import main

if __name__ == "__main__":
    load_dotenv()
    raise SystemExit(main())
