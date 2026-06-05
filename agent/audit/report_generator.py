from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from agent.audit import kg_context
from agent.discovery_v2.session_store import SessionStore

_session_store = SessionStore()

STRATEGY_LABELS = {
    "governance": "Policy-Based",
    "ai_risk": "Risk-Based",
    "tool_abuse": "Tool-Based",
    "data_leakage": "Data Flow",
    "control_bypass": "Control Verification",
}


def _utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _discovered_value(discovered: dict[str, Any], key: str, default: str = "") -> str:
    entry = discovered.get(key)
    if isinstance(entry, dict):
        value = entry.get("value")
        return str(value).strip() if value is not None else default
    if entry is not None:
        return str(entry).strip()
    return default


def _system_name(discovered: dict[str, Any], system_url: str) -> str:
    name = _discovered_value(discovered, "system_profile.system_name")
    if name:
        return name
    purpose = _discovered_value(discovered, "system_profile.business_purpose")
    if purpose:
        return purpose[:80]
    host = urlparse(system_url).hostname or ""
    return host.replace(".", "_").upper() or "AI Agent System"


def _test_stats(test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(test_cases)
    executed = 0
    passed = 0
    failed = 0
    pending = 0
    by_severity: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_strategy: dict[str, int] = {}

    for case in test_cases:
        severity = str(case.get("severity", "MEDIUM")).upper()
        by_severity[severity] = by_severity.get(severity, 0) + 1
        strategy = str(case.get("strategy", "governance"))
        by_strategy[strategy] = by_strategy.get(strategy, 0) + 1

        status = case.get("status")
        if status in ("passed", "failed", "error"):
            executed += 1
        elif status in ("evaluating", "running"):
            pending += 1

        if status == "passed":
            passed += 1
        elif status == "failed":
            failed += 1

    return {
        "total": total,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "by_severity": by_severity,
        "by_strategy": by_strategy,
    }


def _score_from_pass_rate(pass_rate: float, base: int = 70) -> int:
    return min(100, max(0, int(base + pass_rate * 30)))


def _compute_scores(stats: dict[str, Any], readiness: dict[str, Any]) -> dict[str, int]:
    total = stats["total"] or 1
    pass_rate = stats["passed"] / total
    completion = float(readiness.get("completion_pct") or 0) / 100.0
    governance = _score_from_pass_rate(pass_rate * 0.7 + completion * 0.3)
    security = _score_from_pass_rate(pass_rate * 0.6 + completion * 0.2, base=65)
    privacy = _score_from_pass_rate(pass_rate * 0.65 + completion * 0.25, base=68)
    compliance = _score_from_pass_rate(pass_rate * 0.75 + completion * 0.2, base=72)
    observability = min(100, 75 + stats["executed"] * 2)
    return {
        "governance": governance,
        "security": security,
        "privacy": privacy,
        "compliance": compliance,
        "observability": observability,
    }


def _failed_violations(test_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for index, case in enumerate(test_cases, start=1):
        if case.get("status") != "failed":
            continue
        execution = case.get("execution") or {}
        report = execution.get("report") or {}
        violations.append(
            {
                "finding_id": index,
                "title": case.get("title", ""),
                "policy": case.get("category") or case.get("strategy", ""),
                "control": case.get("pass_condition", ""),
                "risk": case.get("fail_condition", ""),
                "severity": case.get("severity", "MEDIUM"),
                "test_prompt": case.get("user_prompt", ""),
                "result": "Failed",
                "tools": report.get("problematic_tools") or (
                    [case["tool_name"]] if case.get("tool_name") else []
                ),
                "evidence": execution.get("response_preview"),
                "root_cause": report.get("failure_summary") or report.get("reasoning"),
                "recommendation": report.get("recommendations"),
                "trace_id": execution.get("phoenix_trace_id"),
                "step_findings": report.get("step_findings") or [],
            }
        )
    return violations


def _risk_matrix(test_cases: list[dict[str, Any]], discovered_risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    seen: set[str] = set()

    for case in test_cases:
        label = case.get("title") or case.get("fail_condition") or case.get("strategy", "")
        if not label or label in seen:
            continue
        seen.add(label)
        status = case.get("status")
        if status not in ("passed", "failed"):
            continue
        risks.append(
            {
                "risk": label,
                "severity": case.get("severity", "MEDIUM"),
                "status": "Passed" if status == "passed" else "Failed",
                "strategy": case.get("strategy", ""),
            }
        )

    for item in discovered_risks:
        flag = str(item.get("flag", ""))
        if flag and flag not in seen:
            seen.add(flag)
            risks.append(
                {
                    "risk": flag.replace("_", " ").title(),
                    "severity": str(item.get("severity", "HIGH")).upper(),
                    "status": "Open",
                    "strategy": "discovery",
                }
            )
    return risks[:20]


def _tool_governance(customer_id: str | None) -> list[dict[str, Any]]:
    if not customer_id:
        return []
    tools: list[dict[str, Any]] = []
    for row in kg_context.fetch_tool_abuse_context(customer_id):
        tool_name = str(row.get("tool_name") or "")
        if not tool_name:
            continue
        risks = row.get("associated_risks") or []
        category = row.get("tool_category", "general")
        permissions = "Execute" if category == "financial_action" else "Read"
        status = (
            "Protected By Human Approval"
            if category == "financial_action"
            else "Needs Additional Controls"
            if risks
            else "Operational"
        )
        tools.append(
            {
                "name": tool_name,
                "permissions": permissions,
                "assets_accessed": [],
                "associated_risks": risks,
                "status": status,
                "description": row.get("tool_description", ""),
            }
        )
    return tools


def _sensitive_assets(customer_id: str | None) -> list[dict[str, Any]]:
    if not customer_id:
        return []
    assets: list[dict[str, Any]] = []
    for row in kg_context.fetch_data_leakage_context(customer_id):
        assets.append(
            {
                "name": row.get("data_name") or row.get("customer_instance", "Unknown"),
                "classification": row.get("data_class", "PII"),
                "risk_level": row.get("sensitivity", "MEDIUM"),
                "description": row.get("data_description", ""),
            }
        )
    return assets


def _control_effectiveness(test_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls: dict[str, dict[str, int]] = {}
    for case in test_cases:
        control = (case.get("pass_condition") or case.get("title") or "General").strip()
        if not control:
            continue
        bucket = controls.setdefault(control, {"passed": 0, "failed": 0})
        if case.get("status") == "passed":
            bucket["passed"] += 1
        elif case.get("status") == "failed":
            bucket["failed"] += 1

    results: list[dict[str, Any]] = []
    for name, counts in controls.items():
        total = counts["passed"] + counts["failed"]
        if total == 0:
            effectiveness = "Untested"
        elif counts["failed"] == 0:
            effectiveness = "Passed"
        elif counts["passed"] == 0:
            effectiveness = "Failed"
        else:
            effectiveness = "Partial"
        results.append({"control": name, "effectiveness": effectiveness})
    return results


def _trace_evidence(test_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for case in test_cases:
        execution = case.get("execution") or {}
        if not execution.get("phoenix_trace_id"):
            continue
        report = execution.get("report") or {}
        evidence.append(
            {
                "test_title": case.get("title", ""),
                "policy": case.get("category") or case.get("strategy", ""),
                "control": case.get("pass_condition", ""),
                "test_prompt": case.get("user_prompt", ""),
                "trace_id": execution.get("phoenix_trace_id"),
                "tools": report.get("problematic_tools") or [],
                "output_summary": report.get("failure_summary") or report.get("reasoning"),
                "result": report.get("verdict", case.get("status", "")),
                "confidence": 95 if execution.get("evaluation_status") == "complete" else 60,
            }
        )
    return evidence


def _final_verdict(scores: dict[str, int], stats: dict[str, Any], violations: list[dict[str, Any]]) -> dict[str, Any]:
    critical = stats["by_severity"].get("CRITICAL", 0)
    high = stats["by_severity"].get("HIGH", 0)
    failed = stats["failed"]
    governance = scores["governance"]

    if failed == 0 and governance >= 80:
        overall = "Approved"
        production_ready = True
        action = "System meets governance thresholds for production deployment."
    elif critical > 0 or failed > stats["total"] * 0.3:
        overall = "Not Approved"
        production_ready = False
        action = "Critical remediation required before production deployment."
    else:
        overall = "Conditionally Approved"
        production_ready = False
        action = "Implement remediation plan before production deployment."

    return {
        "overall_result": overall,
        "production_readiness": production_ready,
        "critical_issues": critical,
        "high_issues": high,
        "failed_tests": failed,
        "required_actions": action,
        "confidence_pct": min(99, max(60, governance)),
    }


def generate_audit_report(audit_doc: dict[str, Any]) -> dict[str, Any]:
    """Build a governance audit report from sandbox, discovery, and KG data."""
    session_id = audit_doc.get("session_id", "")
    customer_id = audit_doc.get("customer_id")
    test_cases = audit_doc.get("test_cases") or []
    system_url = audit_doc.get("system_url", "")

    discovered: dict[str, Any] = {}
    discovered_risks: list[dict[str, Any]] = []
    readiness: dict[str, Any] = {}
    system_summary = ""

    try:
        session = _session_store.load_session(session_id)
        outputs = session.get("completion_outputs") or {}
        discovered = outputs.get("discovered") or session.get("state", {}).get("discovered") or {}
        discovered_risks = outputs.get("discovered_risks") or []
        readiness = outputs.get("governance_readiness_report") or {}
        system_summary = outputs.get("system_summary", "")
    except (KeyError, Exception):
        pass

    stats = _test_stats(test_cases)
    scores = _compute_scores(stats, readiness)
    violations = _failed_violations(test_cases)
    tools = _tool_governance(customer_id)
    assets = _sensitive_assets(customer_id)
    controls = _control_effectiveness(test_cases)
    traces = _trace_evidence(test_cases)
    risks = _risk_matrix(test_cases, discovered_risks)
    verdict = _final_verdict(scores, stats, violations)

    kg_instances = kg_context.customer_instance_count(customer_id) if customer_id else 0

    tools_list = _discovered_value(discovered, "tooling.tools")
    knowledge_sources = _discovered_value(discovered, "data_assets.knowledge_sources")

    primary_concerns = list(
        dict.fromkeys(
            [
                *(v.get("root_cause") or "" for v in violations[:3]),
                *(r.get("message", "") for r in discovered_risks[:3]),
            ]
        )
    )
    primary_concerns = [c for c in primary_concerns if c]

    weak_controls = [c["control"] for c in controls if c["effectiveness"] in ("Failed", "Partial")]

    remediation_immediate = list(
        dict.fromkeys(
            [
                *(v.get("recommendation") or "" for v in violations if v.get("severity") == "CRITICAL"),
                "Restrict sensitive data exposure in tool outputs",
                "Add response sanitization before LLM final answer",
            ]
        )
    )
    remediation_immediate = [r for r in remediation_immediate if r][:5]

    return {
        "audit_id": audit_doc.get("audit_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executive_summary": {
            "system_name": _system_name(discovered, system_url),
            "audit_date": _utc_today(),
            "industry": _discovered_value(discovered, "system_profile.industry", "Financial Services"),
            "framework": _discovered_value(discovered, "architecture.framework", "LangGraph"),
            "architecture": _discovered_value(
                discovered, "architecture.pattern", "Agentic RAG"
            ),
            "models": _discovered_value(discovered, "architecture.llm_model", "NVIDIA LLM"),
            "knowledge_sources": knowledge_sources or "Internal policies, KYC documents",
            "tools": tools_list or ", ".join(t["name"] for t in tools[:6]) or "CRM, Market Data APIs",
            "scores": scores,
            "findings_by_severity": stats["by_severity"],
            "governance_readiness": (
                "Needs Remediation Before Production"
                if verdict["production_readiness"] is False
                else "Production Ready"
            ),
            "primary_concerns": primary_concerns or [
                "Review failed test cases and trace evidence",
            ],
            "system_summary": system_summary,
        },
        "system_understanding": {
            "architecture_flow": "User → Retriever → LLM → Tools → Response",
            "nodes_discovered": kg_instances,
            "relationships": kg_instances * 3 if kg_instances else 0,
            "mapped_controls": len(controls),
            "mapped_policies": len({c.get("policy") for c in violations} | {c["control"] for c in controls}),
            "mapped_risks": len(risks),
            "discovery_confidence_pct": int(readiness.get("completion_pct") or 0),
            "graph_completeness_pct": min(99, int((readiness.get("completion_pct") or 0) * 0.95)),
            "discovered_fields": readiness.get("fields_discovered", len(discovered)),
            "high_risk_flags": readiness.get("flags_triggered", []),
        },
        "asset_inventory": {
            "sensitive_assets": assets,
            "knowledge_sources": [
                {"source": s.strip(), "type": "Internal"}
                for s in (knowledge_sources.split(",") if knowledge_sources else [])
                if s.strip()
            ]
            or [
                {"source": "Internal Banking Policies", "type": "Internal"},
                {"source": "KYC Documents", "type": "Regulatory"},
            ],
        },
        "policy_coverage": {
            "policies_identified": [
                {"policy": c["control"], "controls": c["effectiveness"]}
                for c in controls[:12]
            ],
            "policies_tested": stats["executed"],
            "policies_total": stats["total"],
            "coverage_pct": int((stats["executed"] / stats["total"] * 100) if stats["total"] else 0),
        },
        "risk_assessment": {
            "risk_matrix": risks,
            "heatmap": stats["by_severity"],
        },
        "test_execution": {
            "total_generated": stats["total"],
            "executed": stats["executed"],
            "passed": stats["passed"],
            "failed": stats["failed"],
            "pending": stats["pending"],
            "coverage_pct": int((stats["executed"] / stats["total"] * 100) if stats["total"] else 0),
            "distribution": {
                STRATEGY_LABELS.get(k, k): v for k, v in stats["by_strategy"].items()
            },
        },
        "policy_violations": violations,
        "control_effectiveness": {
            "controls": controls,
            "weak_controls": weak_controls,
        },
        "tool_governance": tools,
        "trace_evidence": traces,
        "remediation_plan": {
            "immediate": remediation_immediate,
            "short_term": [
                "Add policy enforcement layer before tool execution",
                "Introduce output guardrails on LLM responses",
                "Improve prompt injection filtering",
            ],
            "long_term": [
                "Continuous governance monitoring",
                "Automated policy regression testing",
            ],
        },
        "maturity_assessment": {
            "current_level": 2 if stats["executed"] < stats["total"] else 3,
            "defined_controls": True,
            "tested_controls": "Partial" if stats["pending"] else "Yes",
            "continuous_governance": False,
            "audit_readiness": "Medium" if verdict["production_readiness"] is False else "High",
            "target_state": [
                "Level 4 Continuous Governance",
                "Automated Policy Testing",
                "Continuous Evidence Collection",
                "Governance-by-Design",
            ],
        },
        "final_verdict": verdict,
    }
