"""Map discovery session JSON to customer KG (Neo4j + Mongo audit).

Usage:
    uv run python scripts/map_kg_from_session_file.py \\
        --session-file ../discovery_session.json \\
        --customer-id 2a356777-527a-483f-b3a5-fa3465a79074
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

from dataclasses import asdict

from agent.api.mongo.kg_repository import save_mapping_run
from agent.knowledge_graph.kg_mapper import run_mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Map discovery JSON to customer knowledge graph")
    parser.add_argument("--session-file", type=Path, required=True)
    parser.add_argument("--customer-id", required=True)
    parser.add_argument("--replace-existing", action="store_true")
    args = parser.parse_args()

    doc = json.loads(args.session_file.read_text(encoding="utf-8"))
    discovered = doc.get("state", {}).get("discovered", {})
    session_id = doc.get("session_id", "")

    result = run_mapping(
        args.customer_id,
        source_type="discovery",
        session_id=session_id,
        discovered=discovered,
        replace_existing=args.replace_existing,
    )
    save_mapping_run(
        {
            "mapping_run_id": result.mapping_run_id,
            "customer_id": result.customer_id,
            "source": result.source,
            "entities": [asdict(e) for e in result.entities],
            "mapped_count": result.mapped_count,
            "skipped_count": result.skipped_count,
            "low_confidence": result.low_confidence,
            "neo4j_stats": result.neo4j_stats,
            "created_at": result.created_at,
        }
    )

    print(f"mapped_count={result.mapped_count} skipped_count={result.skipped_count}")
    print(f"neo4j_stats={result.neo4j_stats}")
    for entity in result.entities:
        print(f"  {entity.source_value} -> {entity.ontology_name} ({entity.match_score:.2f})")
    if result.low_confidence:
        print("low_confidence:")
        for row in result.low_confidence[:10]:
            print(f"  {row}")
    return 0 if result.mapped_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
