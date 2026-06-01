from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .client import neo4j_session
from .config import DEFAULT_CYPHER_FILE, Neo4jSettings
from .parser import parse_cypher_file

WIPE_ONTOLOGY = "MATCH (n:OntologyNode) DETACH DELETE n"


def wipe_ontology(session) -> None:
    session.run(WIPE_ONTOLOGY)


def load_cypher_file(
    cypher_path: Path,
    *,
    settings: Neo4jSettings | None = None,
    wipe: bool = True,
) -> int:
    """Load the full Cypher ontology file into Neo4j. Returns statement count."""
    settings = settings or Neo4jSettings.from_env()
    statements = parse_cypher_file(cypher_path)

    with neo4j_session(settings) as session:
        if wipe:
            wipe_ontology(session)

        for index, statement in enumerate(statements, start=1):
            session.run(statement)

    return len(statements)


def verify_load(settings: Neo4jSettings | None = None) -> dict[str, int]:
    settings = settings or Neo4jSettings.from_env()
    with neo4j_session(settings) as session:
        node_count = session.run(
            "MATCH (n:OntologyNode) RETURN count(n) AS count"
        ).single()["count"]
        rel_count = session.run(
            "MATCH (:OntologyNode)-[r]->(:OntologyNode) RETURN count(r) AS count"
        ).single()["count"]
    return {"nodes": node_count, "relationships": rel_count}


def main(argv: list[str] | None = None) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Load the FinTech AI governance knowledge graph into Neo4j."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_CYPHER_FILE,
        help=f"Path to the Cypher file (default: {DEFAULT_CYPHER_FILE.name})",
    )
    parser.add_argument(
        "--no-wipe",
        action="store_true",
        help="Do not delete existing :OntologyNode data before loading",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Print node/relationship counts after loading",
    )
    args = parser.parse_args(argv)

    try:
        count = load_cypher_file(args.file, wipe=not args.no_wipe)
        print(f"Loaded {count} Cypher statements from {args.file}")

        if args.verify:
            stats = verify_load()
            print(f"Ontology nodes: {stats['nodes']}")
            print(f"Ontology relationships: {stats['relationships']}")

        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
