from __future__ import annotations

from pathlib import Path


def parse_cypher_file(path: Path) -> list[str]:
    """Split a Cypher script into executable statements (skips comment-only lines)."""
    if not path.is_file():
        raise FileNotFoundError(f"Cypher file not found: {path}")

    statements: list[str] = []
    buffer: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        buffer.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []

    if buffer:
        trailing = "\n".join(buffer).strip()
        if trailing:
            raise ValueError(
                f"Incomplete Cypher statement at end of {path.name} "
                "(missing terminating semicolon)"
            )

    return statements
