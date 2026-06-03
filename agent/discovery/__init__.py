"""Jupiter Discovery Agent — conversational system profiling."""

__all__ = ["create_session", "process_turn"]


def __getattr__(name: str):
    if name in {"create_session", "process_turn"}:
        from agent.discovery.orchestrator import create_session, process_turn

        return create_session if name == "create_session" else process_turn
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
