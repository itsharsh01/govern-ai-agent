from __future__ import annotations

"""
Google ADK agent definition for Jupiter Discovery.

The production API uses turn_runner.run_turn (deterministic tool pipeline).
This module exposes the same tools on an ADK LlmAgent for ADK CLI / dev UI.
"""

from agent.discovery_v2.config import discovery_llm_model

try:
    from google.adk.agents import Agent

    def build_discovery_agent() -> Agent:
        return Agent(
            name="jupiter_discovery",
            model=discovery_llm_model(),
            instruction=(
                "You are the Jupiter governance discovery agent. "
                "On each user message, use tools in order: parse_answer, apply state updates "
                "via the API runner, peek_queue, check_confidence, generate_question. "
                "Ask exactly one question per turn. Handle clarifications without advancing the queue."
            ),
            description="Governance discovery interviewer for AI systems",
            tools=[],  # Tools invoked by turn_runner; extend with FunctionTool wrappers as needed
        )

    root_agent = build_discovery_agent()
except ImportError:
    root_agent = None  # type: ignore[misc, assignment]
