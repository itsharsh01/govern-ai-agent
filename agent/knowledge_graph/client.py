from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from neo4j import Driver, GraphDatabase, Session

from .config import Neo4jSettings


def create_driver(settings: Neo4jSettings) -> Driver:
    try:
        driver = GraphDatabase.driver(
            settings.uri,
            auth=(settings.user, settings.password),
            connection_timeout=30,
        )
        driver.verify_connectivity()
        return driver
    except Exception as exc:
        message = str(exc)
        if "Unable to retrieve routing information" in message:
            raise ConnectionError(
                "Neo4j connection failed (routing/SSL). Common fixes:\n"
                "  1. Use neo4j+ssc:// instead of neo4j+s:// in NEO4J_URI, or set NEO4J_SSL_TRUST_ALL=1\n"
                "     (needed on some Windows/VPN/corporate networks)\n"
                "  2. Confirm NEO4J_USER and NEO4J_PASSWORD from the Aura console\n"
                "  3. Ensure the Aura instance is running (not paused)"
            ) from exc
        raise


@contextmanager
def neo4j_session(settings: Neo4jSettings) -> Iterator[Session]:
    driver = create_driver(settings)
    try:
        database = settings.database or "neo4j"
        with driver.session(database=database) as session:
            yield session
    finally:
        driver.close()
