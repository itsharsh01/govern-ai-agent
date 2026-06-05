from __future__ import annotations

from agent.api.schemas import (
    ApplicationType,
    CustomerRecord,
    Environment,
    SensitiveDataAsset,
    SystemInformationRecord,
    ToolCategory,
    ToolRecord,
)
from agent.knowledge_graph.entity_extractor import extract_from_customer, extract_from_discovery


def test_extract_tools_from_discovery():
    discovered = {
        "tooling.tools": {
            "value": [
                {
                    "tool_name": "CustomerInsightEngine",
                    "tool_description": "CRM profile lookup",
                    "access_required": "read customers",
                    "access_currently_has": "sandbox",
                }
            ],
            "confidence": 0.95,
        }
    }
    entities = extract_from_discovery(discovered)
    assert len(entities) == 1
    assert entities[0].display_name == "CustomerInsightEngine"
    assert entities[0].entity_type == "tool"
    assert entities[0].node_types == ("AgentTool",)
    assert "CRM profile lookup" in entities[0].search_text


def test_extract_data_assets_from_customer():
    record = CustomerRecord(
        id="cust-1",
        name="Acme",
        email="ops@acme.com",
        tools=[
            ToolRecord(
                name="Stripe API",
                description="Payments",
                category=ToolCategory.PAYMENT,
            )
        ],
        sensitive_data_assets=[
            SensitiveDataAsset.CUSTOMER_EMAIL,
            SensitiveDataAsset.ACCOUNT_NUMBER,
        ],
        system_information=SystemInformationRecord(
            application_name="Support Bot",
            application_description="Handles customer support",
            application_type=ApplicationType.CUSTOMER_SUPPORT_AGENT,
            environment=Environment.PRODUCTION,
        ),
    )
    entities = extract_from_customer(record)
    names = {entity.display_name for entity in entities}
    assert "Stripe API" in names
    assert "Customer Email" in names
    assert "Account Number" in names
    assert "Support Bot" in names
