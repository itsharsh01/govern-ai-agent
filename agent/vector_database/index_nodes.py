"""Index all Neo4j ontology nodes into Qdrant with local embeddings.

    uv run python agent/vector_database/index_nodes.py
    uv run python agent/vector_database/index_nodes.py --recreate
    uv run python agent/vector_database/index_nodes.py --dry-run
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from agent.vector_database.config import QdrantSettings
from agent.vector_database.embedder import DEFAULT_MODEL
from agent.vector_database.indexer import index_ontology_nodes


def main(argv: list[str] | None = None) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Embed ontology nodes and store in Qdrant")
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate collection")
    parser.add_argument("--dry-run", action="store_true", help="Print sample texts only")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="sentence-transformers model")
    args = parser.parse_args(argv)

    try:
        settings = QdrantSettings.from_env()
        model = args.model if args.model != DEFAULT_MODEL else settings.embedding_model
        result = index_ontology_nodes(
            qdrant_settings=settings,
            model_name=model,
            recreate=args.recreate,
            dry_run=args.dry_run,
        )

        if result.get("dry_run"):
            print(f"Dry run: {result['count']} nodes")
            for i, sample in enumerate(result["samples"], 1):
                print(f"\n--- Sample {i} ---\n{sample}...")
            return 0

        print(f"Indexed {result['indexed']} nodes -> {result['collection']}")
        print(f"  model: {result['model']}")
        print(f"  vector size: {result['vector_size']}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
