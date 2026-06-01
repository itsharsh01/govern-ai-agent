"""Export ontology graph to JSON for the HTML viewer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent.knowledge_graph.client import neo4j_session
from agent.knowledge_graph.config import Neo4jSettings

GRAPH_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = GRAPH_DIR / "graph_data.json"

NODE_QUERY = """
MATCH (n:OntologyNode)
RETURN elementId(n) AS id,
       labels(n) AS labels,
       n.name AS name,
       n.category AS category,
       n.risk AS risk,
       properties(n) AS props
"""

EDGE_QUERY = """
MATCH (a:OntologyNode)-[r]->(b:OntologyNode)
RETURN elementId(a) AS source,
       elementId(b) AS target,
       type(r) AS rel_type
"""

LABEL_COLORS = {
    "SensitiveFinancialData": "#e74c3c",
    "PersonalInformation": "#e67e22",
    "AgentTool": "#3498db",
    "AISecurityRisk": "#9b59b6",
    "PrivacyRisk": "#8e44ad",
    "ComplianceControl": "#27ae60",
    "BankingRegulation": "#16a085",
    "GovernanceRequirement": "#2ecc71",
    "AIAgent": "#f39c12",
    "OntologyNode": "#95a5a6",
}


def _primary_label(labels: list[str]) -> str:
    for label in labels:
        if label != "OntologyNode":
            return label
    return labels[0] if labels else "OntologyNode"


def fetch_graph(settings: Neo4jSettings | None = None) -> dict:
    settings = settings or Neo4jSettings.from_env()
    nodes: list[dict] = []
    edges: list[dict] = []

    with neo4j_session(settings) as session:
        for record in session.run(NODE_QUERY):
            labels = list(record["labels"] or [])
            primary = _primary_label(labels)
            name = record["name"] or "(unnamed)"
            nodes.append(
                {
                    "id": record["id"],
                    "label": name,
                    "title": _node_tooltip(name, labels, record["props"] or {}),
                    "group": primary,
                    "color": LABEL_COLORS.get(primary, LABEL_COLORS["OntologyNode"]),
                    "category": record["category"],
                    "risk": record["risk"],
                }
            )

        for record in session.run(EDGE_QUERY):
            edges.append(
                {
                    "from": record["source"],
                    "to": record["target"],
                    "label": record["rel_type"],
                    "arrows": "to",
                    "font": {"size": 9, "align": "middle"},
                }
            )

    return {"nodes": nodes, "edges": edges}


def _node_tooltip(name: str, labels: list[str], props: dict) -> str:
    lines = [f"<b>{name}</b>", f"Labels: {', '.join(labels)}"]
    for key in ("category", "risk", "description"):
        if props.get(key):
            val = str(props[key])
            if len(val) > 200:
                val = val[:200] + "…"
            lines.append(f"{key}: {val}")
    return "<br>".join(lines)


def export_graph(output: Path = DEFAULT_OUTPUT) -> Path:
    data = fetch_graph()
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    output = DEFAULT_OUTPUT
    if argv and len(argv) > 1:
        output = Path(argv[1])

    try:
        path = export_graph(output)
        print(f"Exported {path.stat().st_size:,} bytes -> {path}")
        print(f"  nodes: {len(json.loads(path.read_text())['nodes'])}")
        print(f"  edges: {len(json.loads(path.read_text())['edges'])}")
        print(f"\nOpen viewer:\n  cd {GRAPH_DIR}\n  python -m http.server 8080")
        print("  http://localhost:8080/view_graph.html")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
