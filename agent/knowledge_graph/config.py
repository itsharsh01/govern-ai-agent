from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_CYPHER_FILE = (
    Path(__file__).resolve().parent / "data" / "fintech_ai_governance_neo4j.cypher"
)

AURA_HOST_SUFFIX = ".databases.neo4j.io"


def _get_env(key: str, default: str = "") -> str:
    value = os.environ.get(key, default).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


def _is_truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def _normalize_uri(uri: str) -> str:
    """Aura on Windows/VPN often needs +ssc instead of +s for TLS."""
    if _is_truthy(_get_env("NEO4J_SSL_STRICT")):
        return uri

    use_trust_all = _is_truthy(_get_env("NEO4J_SSL_TRUST_ALL"))
    host = urlparse(uri).hostname or ""
    is_aura = host.endswith(AURA_HOST_SUFFIX)

    if use_trust_all or is_aura:
        uri = uri.replace("neo4j+s://", "neo4j+ssc://").replace(
            "bolt+s://", "bolt+ssc://"
        )
    return uri


def _default_aura_database(uri: str) -> str | None:
    host = urlparse(uri).hostname or ""
    if host.endswith(AURA_HOST_SUFFIX):
        return host[: -len(AURA_HOST_SUFFIX)]
    return None


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    user: str
    password: str
    database: str | None = None

    @classmethod
    def from_env(cls) -> Neo4jSettings:
        password = _get_env("NEO4J_PASSWORD")
        if not password:
            raise ValueError(
                "NEO4J_PASSWORD is required. Set it in .env or the environment."
            )

        uri = _normalize_uri(_get_env("NEO4J_URI", "bolt://localhost:7687"))
        user = _get_env("NEO4J_USER", "neo4j")
        database = _get_env("NEO4J_DATABASE") or _default_aura_database(uri) or "neo4j"

        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
        )
