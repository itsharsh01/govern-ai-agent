from __future__ import annotations

import logging
from typing import Any

from agent.knowledge_graph.client import neo4j_session
from agent.knowledge_graph.config import Neo4jSettings

logger = logging.getLogger(__name__)

CONTEXT_LIMIT = 20

CYPHER_INSTANCE_COUNT = """
MATCH (g:CustomerGraph {customer_id: $customer_id})-[:HAS_INSTANCE]->(ci:CustomerInstance)
RETURN count(ci) AS instance_count
"""

# Governance: all ontology AIAgents governed by regulations, optionally anchored to
# customer's mapped tools (if customer has no AIAgent instances, we use the full ontology).
CYPHER_GOVERNANCE = """
MATCH (reg:OntologyNode)-[:GOVERNS]->(agent:OntologyNode)
WHERE 'BankingRegulation' IN labels(reg) AND 'AIAgent' IN labels(agent)
OPTIONAL MATCH (req:OntologyNode)-[:GOVERNS]->(agent)
WHERE 'GovernanceRequirement' IN labels(req)
WITH agent, collect(DISTINCT reg.name) AS regulations,
     collect(DISTINCT req.name) AS requirements
RETURN agent.name AS agent_name,
       coalesce(agent.description, agent.name) AS agent_purpose,
       regulations,
       requirements
LIMIT $limit
"""

# AI Risk: ontology AIAgents targeted by AISecurityRisks, with tools they use
CYPHER_AI_RISK = """
MATCH (risk:OntologyNode)-[:TARGETS]->(agent:OntologyNode)
WHERE 'AISecurityRisk' IN labels(risk) AND 'AIAgent' IN labels(agent)
OPTIONAL MATCH (tool:OntologyNode)-[:USED_BY]->(agent)
WHERE 'AgentTool' IN labels(tool)
WITH agent, risk, collect(DISTINCT tool.name) AS tools
RETURN agent.name AS agent_name,
       coalesce(agent.description, agent.name) AS agent_purpose,
       risk.name AS risk_name,
       coalesce(risk.description, risk.name) AS risk_description,
       coalesce(risk.category, '') AS risk_category,
       risk.attack_vectors AS attack_vectors,
       risk.owasp_llm AS owasp_llm,
       tools
LIMIT $limit
"""

# Tool Abuse: customer's mapped tool instances -> ontology tool -> agents that use it.
# Relationship direction: (tool:AgentTool)-[:USED_BY]->(agent:AIAgent)
CYPHER_TOOL_ABUSE = """
MATCH (g:CustomerGraph {customer_id: $customer_id})-[:HAS_INSTANCE]->(ci_tool:CustomerInstance)
      -[:INSTANCE_OF]->(tool:OntologyNode)
WHERE 'AgentTool' IN labels(tool)
OPTIONAL MATCH (tool)-[:USED_BY]->(agent:OntologyNode)
WHERE 'AIAgent' IN labels(agent)
OPTIONAL MATCH (risk:OntologyNode)-[:TARGETS]->(tool)
WHERE 'AISecurityRisk' IN labels(risk)
WITH ci_tool, tool, agent, collect(DISTINCT risk.name) AS associated_risks
RETURN ci_tool.display_name AS customer_instance,
       tool.name AS tool_name,
       coalesce(tool.description, tool.name) AS tool_description,
       coalesce(agent.name, 'unknown') AS agent_name,
       coalesce(agent.description, agent.name, 'N/A') AS agent_purpose,
       associated_risks
LIMIT $limit
"""

# Tool Abuse fallback: when customer has no tool CIs, use all ontology tools
CYPHER_TOOL_ABUSE_FALLBACK = """
MATCH (tool:OntologyNode)-[:USED_BY]->(agent:OntologyNode)
WHERE 'AgentTool' IN labels(tool) AND 'AIAgent' IN labels(agent)
OPTIONAL MATCH (risk:OntologyNode)-[:TARGETS]->(tool)
WHERE 'AISecurityRisk' IN labels(risk)
WITH tool, agent, collect(DISTINCT risk.name) AS associated_risks
RETURN 'ontology' AS customer_instance,
       tool.name AS tool_name,
       coalesce(tool.description, tool.name) AS tool_description,
       agent.name AS agent_name,
       coalesce(agent.description, agent.name) AS agent_purpose,
       associated_risks
LIMIT $limit
"""

# Data Leakage: customer's mapped data_asset instances -> ontology data -> agents that access it.
# Relationship direction: (data)-[:ACCESSED_BY]->(agent)
CYPHER_DATA_LEAKAGE = """
MATCH (g:CustomerGraph {customer_id: $customer_id})-[:HAS_INSTANCE]->(ci_data:CustomerInstance)
      -[:INSTANCE_OF]->(data:OntologyNode)
WHERE 'PersonalInformation' IN labels(data) OR 'SensitiveFinancialData' IN labels(data)
OPTIONAL MATCH (data)-[:ACCESSED_BY]->(agent:OntologyNode)
WHERE 'AIAgent' IN labels(agent)
OPTIONAL MATCH (tool:OntologyNode)-[:USED_BY]->(agent)
WHERE 'AgentTool' IN labels(tool)
WITH ci_data, data, agent, collect(DISTINCT tool.name) AS tools
RETURN ci_data.display_name AS customer_instance,
       data.name AS data_name,
       coalesce(data.description, data.name) AS data_description,
       CASE WHEN 'SensitiveFinancialData' IN labels(data) THEN 'SFD' ELSE 'PII' END AS data_class,
       coalesce(agent.name, 'unknown') AS agent_name,
       coalesce(agent.description, agent.name, 'N/A') AS agent_purpose,
       tools
LIMIT $limit
"""

# Data Leakage via CAN_ACCESS edges on customer instances
CYPHER_DATA_LEAKAGE_CAN_ACCESS = """
MATCH (g:CustomerGraph {customer_id: $customer_id})-[:HAS_INSTANCE]->(ci:CustomerInstance)
      -[:CAN_ACCESS]->(data:OntologyNode)
WHERE 'PersonalInformation' IN labels(data) OR 'SensitiveFinancialData' IN labels(data)
OPTIONAL MATCH (data)-[:ACCESSED_BY]->(agent:OntologyNode)
WHERE 'AIAgent' IN labels(agent)
OPTIONAL MATCH (tool:OntologyNode)-[:USED_BY]->(agent)
WHERE 'AgentTool' IN labels(tool)
WITH ci, data, agent, collect(DISTINCT tool.name) AS tools
RETURN ci.display_name AS customer_instance,
       data.name AS data_name,
       coalesce(data.description, data.name) AS data_description,
       CASE WHEN 'SensitiveFinancialData' IN labels(data) THEN 'SFD' ELSE 'PII' END AS data_class,
       coalesce(agent.name, 'unknown') AS agent_name,
       coalesce(agent.description, agent.name, 'N/A') AS agent_purpose,
       tools
LIMIT $limit
"""

# Control Bypass: risks -> controls, using all ontology agents (not customer-scoped)
CYPHER_CONTROL_BYPASS = """
MATCH (risk:OntologyNode)-[:MITIGATED_BY]->(ctrl:OntologyNode)
WHERE 'ComplianceControl' IN labels(ctrl)
OPTIONAL MATCH (risk)-[:TARGETS]->(agent:OntologyNode)
WHERE 'AIAgent' IN labels(agent)
OPTIONAL MATCH (ctrl)-[:REQUIRED_BY]->(reg:OntologyNode)
WITH ctrl, risk, agent, collect(DISTINCT reg.name) AS regulations
RETURN coalesce(agent.name, 'general') AS agent_name,
       coalesce(agent.description, agent.name, 'AI system') AS agent_purpose,
       ctrl.name AS control_name,
       coalesce(ctrl.description, ctrl.name) AS control_claim,
       coalesce(regulations[0], 'Internal policy') AS regulation_name,
       collect(DISTINCT risk.name) AS mitigated_risks
LIMIT $limit
"""


def _run_query(
    cypher: str,
    *,
    customer_id: str,
    settings: Neo4jSettings | None = None,
) -> list[dict[str, Any]]:
    settings = settings or Neo4jSettings.from_env()
    try:
        with neo4j_session(settings) as session:
            result = session.run(
                cypher,
                customer_id=customer_id,
                limit=CONTEXT_LIMIT,
            )
            return [dict(record) for record in result]
    except Exception as exc:
        logger.warning("Neo4j query failed for customer %s: %s", customer_id, exc)
        return []


def customer_instance_count(
    customer_id: str,
    settings: Neo4jSettings | None = None,
) -> int:
    settings = settings or Neo4jSettings.from_env()
    try:
        with neo4j_session(settings) as session:
            record = session.run(
                CYPHER_INSTANCE_COUNT,
                customer_id=customer_id,
            ).single()
            return int(record["instance_count"] if record else 0)
    except Exception as exc:
        logger.warning("Neo4j instance count failed for %s: %s", customer_id, exc)
        return 0


def fetch_governance_context(customer_id: str) -> list[dict[str, Any]]:
    return _run_query(CYPHER_GOVERNANCE, customer_id=customer_id)


def fetch_ai_risk_context(customer_id: str) -> list[dict[str, Any]]:
    return _run_query(CYPHER_AI_RISK, customer_id=customer_id)


def classify_tool_category(tool_name: str) -> str:
    name = tool_name.lower()
    if any(k in name for k in ("payment", "transaction", "transfer")):
        return "financial_action"
    if any(k in name for k in ("search", "retrieval", "query", "lookup", "crm")):
        return "data_retrieval"
    if any(k in name for k in ("email", "notification", "message")):
        return "communication"
    if any(k in name for k in ("kyc", "identity", "verification")):
        return "identity_verification"
    if any(k in name for k in ("api", "external", "webhook")):
        return "external_integration"
    return "general"


def fetch_tool_abuse_context(customer_id: str) -> list[dict[str, Any]]:
    rows = _run_query(CYPHER_TOOL_ABUSE, customer_id=customer_id)
    # Deduplicate by tool_name
    seen: set[str] = set()
    unique_rows = []
    for row in rows:
        key = str(row.get("tool_name", ""))
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
    rows = unique_rows
    # If no agent connections found for customer tools, enrich with ontology tool context
    has_agent = any(r.get("agent_name", "unknown") != "unknown" for r in rows)
    if not rows or not has_agent:
        ontology_rows = _run_query(CYPHER_TOOL_ABUSE_FALLBACK, customer_id=customer_id)
        # Merge: keep customer rows but supplement with ontology rows for known tool names
        customer_tool_names = {r.get("tool_name") for r in rows}
        for row in ontology_rows:
            if row.get("tool_name") not in customer_tool_names:
                rows.append(row)
            else:
                # enrich matching customer row with agent info from ontology
                for cr in rows:
                    if cr.get("tool_name") == row.get("tool_name"):
                        cr.setdefault("agent_name", row.get("agent_name"))
                        cr.setdefault("agent_purpose", row.get("agent_purpose"))
                        if not cr.get("associated_risks"):
                            cr["associated_risks"] = row.get("associated_risks", [])
    for row in rows:
        row["tool_category"] = classify_tool_category(str(row.get("tool_name") or ""))
    return rows


def score_data_sensitivity(data_name: str, data_class: str) -> str:
    name = data_name.lower()
    if data_class == "SFD" and any(k in name for k in ("pan", "account_number", "card")):
        return "CRITICAL"
    if data_class == "SFD":
        return "HIGH"
    if data_class == "PII" and any(k in name for k in ("identity", "passport", "aadhaar")):
        return "HIGH"
    return "MEDIUM"


def fetch_data_leakage_context(customer_id: str) -> list[dict[str, Any]]:
    rows = _run_query(CYPHER_DATA_LEAKAGE, customer_id=customer_id)
    if not rows:
        # fallback: use CAN_ACCESS edges on customer tool/data instances
        rows = _run_query(CYPHER_DATA_LEAKAGE_CAN_ACCESS, customer_id=customer_id)
    for row in rows:
        row["sensitivity"] = score_data_sensitivity(
            str(row.get("data_name") or ""),
            str(row.get("data_class") or "PII"),
        )
    return rows


def fetch_control_bypass_context(customer_id: str) -> list[dict[str, Any]]:
    return _run_query(CYPHER_CONTROL_BYPASS, customer_id=customer_id)
