from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from agent.audit import kg_context
from agent.audit.normalize import normalize_test_cases
from agent.audit.prompt_builder import build_strategy_prompt
from agent.discovery_v2.llm import generate_json

logger = logging.getLogger(__name__)

StrategyFetcher = Callable[[str], list[dict[str, Any]]]

STRATEGIES: list[tuple[str, StrategyFetcher]] = [
    ("governance", kg_context.fetch_governance_context),
    ("ai_risk", kg_context.fetch_ai_risk_context),
    ("tool_abuse", kg_context.fetch_tool_abuse_context),
    ("data_leakage", kg_context.fetch_data_leakage_context),
    ("control_bypass", kg_context.fetch_control_bypass_context),
]


@dataclass
class GenerationResult:
    test_cases: list[dict[str, Any]] = field(default_factory=list)
    strategies_generated: list[str] = field(default_factory=list)
    strategies_skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _generate_strategy(
    strategy: str,
    fetcher: StrategyFetcher,
    customer_id: str,
) -> tuple[list[dict[str, Any]], str | None]:
    context = fetcher(customer_id)
    if not context:
        return [], f"No graph context for strategy '{strategy}'"

    prompt = build_strategy_prompt(strategy, context)
    raw = generate_json(prompt)
    if not raw:
        return [], f"LLM returned empty JSON for strategy '{strategy}'"

    cases = normalize_test_cases(strategy, raw, context)
    if not cases:
        return [], f"Could not parse test cases for strategy '{strategy}'"
    return cases, None


def generate_all_strategies(customer_id: str) -> GenerationResult:
    result = GenerationResult()

    for strategy, fetcher in STRATEGIES:
        try:
            cases, warning = _generate_strategy(strategy, fetcher, customer_id)
        except Exception as exc:
            logger.exception("Strategy %s failed", strategy)
            result.warnings.append(f"{strategy}: {exc}")
            result.strategies_skipped.append(strategy)
            continue

        if warning:
            logger.info("Skipping strategy %s: %s", strategy, warning)
            result.warnings.append(warning)
            result.strategies_skipped.append(strategy)
            continue

        result.test_cases.extend(cases)
        result.strategies_generated.append(strategy)

    return result
