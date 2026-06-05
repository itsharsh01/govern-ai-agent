from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import uuid4

from agent.api.schemas import CustomerRecord, SensitiveDataAsset

EntityType = Literal["tool", "data_asset", "agent"]

TOOL_NODE_TYPES = ("AgentTool",)
DATA_NODE_TYPES = ("SensitiveFinancialData", "PersonalInformation")
AGENT_NODE_TYPES = ("AIAgent",)

PII_CATEGORY_SEARCH: dict[str, tuple[str, tuple[str, ...]]] = {
    "email": ("Customer email addresses for notifications and contact", ("PersonalInformation",)),
    "phone": ("Phone numbers for MFA and customer contact", ("PersonalInformation",)),
    "bank_account": ("Bank account numbers and account identifiers", ("SensitiveFinancialData",)),
    "card_number": ("Payment card numbers PAN and cardholder data", ("SensitiveFinancialData",)),
    "credit_score": ("Credit score and risk profile data", ("SensitiveFinancialData",)),
    "name": ("Customer full name and identity PII", ("PersonalInformation",)),
    "national_id": ("National ID and government identity numbers", ("PersonalInformation",)),
    "address": ("Customer residential address PII", ("PersonalInformation",)),
}

DATA_TYPE_SEARCH: dict[str, tuple[str, tuple[str, ...]]] = {
    "customer_pii": ("Customer PII personal identifiable information", ("PersonalInformation",)),
    "transaction_history": (
        "Account balance and transaction history ledger data",
        ("SensitiveFinancialData",),
    ),
    "financial_data": (
        "Sensitive financial data balances and transactions",
        ("SensitiveFinancialData",),
    ),
    "credit_data": ("Credit score and credit risk profile", ("SensitiveFinancialData",)),
    "kyc_documents": ("KYC identity verification documents", ("PersonalInformation",)),
    "investment_portfolio": (
        "Investment portfolio holdings and positions",
        ("SensitiveFinancialData",),
    ),
    "account_data": (
        "Account balance and transaction history",
        ("SensitiveFinancialData",),
    ),
    "employment_data": ("Employment and income data about customers", ("PersonalInformation",)),
    "market_data": ("Market data and securities pricing feeds", ("SensitiveFinancialData",)),
    "internal_documents": (
        "Internal policy and operational documents",
        ("PersonalInformation",),
    ),
}

DATA_ASSET_SEARCH_HINTS: dict[str, tuple[str, tuple[str, ...]]] = {
    SensitiveDataAsset.CUSTOMER_EMAIL.value: (
        "Customer email addresses and contact email for notifications",
        ("PersonalInformation",),
    ),
    SensitiveDataAsset.PHONE_NUMBER.value: (
        "Customer phone numbers for MFA and support",
        ("PersonalInformation",),
    ),
    SensitiveDataAsset.ACCOUNT_NUMBER.value: (
        "Customer bank account numbers and account identifiers",
        ("SensitiveFinancialData",),
    ),
    SensitiveDataAsset.TRANSACTION_HISTORY.value: (
        "Transaction history and payment records",
        ("SensitiveFinancialData",),
    ),
    SensitiveDataAsset.BALANCE_INFORMATION.value: (
        "Account balance information",
        ("SensitiveFinancialData",),
    ),
    SensitiveDataAsset.CREDIT_SCORE.value: (
        "Credit score and risk profile data",
        ("SensitiveFinancialData",),
    ),
    SensitiveDataAsset.KYC_DOCUMENTS.value: (
        "KYC identity documents and verification files",
        ("PersonalInformation",),
    ),
    SensitiveDataAsset.PAN.value: (
        "Permanent account number tax identifier",
        ("PersonalInformation",),
    ),
    SensitiveDataAsset.AADHAAR.value: (
        "National identity Aadhaar number",
        ("PersonalInformation",),
    ),
    SensitiveDataAsset.LOAN_INFORMATION.value: (
        "Loan application and loan account information",
        ("SensitiveFinancialData",),
    ),
}


@dataclass(frozen=True)
class MappableEntity:
    entity_id: str
    source_key: str
    display_name: str
    search_text: str
    entity_type: EntityType
    node_types: tuple[str, ...]
    raw_value: Any = None


def _discovered_value(discovered: dict[str, Any], key: str) -> Any:
    entry = discovered.get(key)
    if entry is None:
        return None
    if isinstance(entry, dict) and "value" in entry:
        return entry["value"]
    return entry


def _tool_search_text(tool: dict[str, Any]) -> str:
    name = str(tool.get("tool_name") or tool.get("name") or "").strip()
    description = str(tool.get("tool_description") or tool.get("description") or "").strip()
    access_required = str(tool.get("access_required") or "").strip()
    parts = [f"Tool: {name}"]
    if description:
        parts.append(description)
    if access_required:
        parts.append(f"Access required: {access_required}")
    return ". ".join(parts)


def _append_tool_entity(
    entities: list[MappableEntity],
    *,
    source_key: str,
    name: str,
    description: str = "",
    raw_value: Any = None,
) -> None:
    name = name.strip()
    if not name:
        return
    tool_payload = (
        {"tool_name": name, "tool_description": description}
        if isinstance(raw_value, dict)
        else raw_value
    )
    entities.append(
        MappableEntity(
            entity_id=f"tool-{uuid4().hex[:8]}",
            source_key=source_key,
            display_name=name,
            search_text=_tool_search_text(
                tool_payload if isinstance(tool_payload, dict) else {"tool_name": name, "tool_description": description}
            ),
            entity_type="tool",
            node_types=TOOL_NODE_TYPES,
            raw_value=raw_value if raw_value is not None else name,
        )
    )


def _extract_tools_from_discovered(
    discovered: dict[str, Any],
    entities: list[MappableEntity],
) -> None:
    tools = _discovered_value(discovered, "tooling.tools")
    if isinstance(tools, str) and tools.strip():
        _append_tool_entity(
            entities,
            source_key="tooling.tools",
            name=tools.strip(),
            description=str(_discovered_value(discovered, "system_profile.system_description") or ""),
            raw_value=tools,
        )
    elif isinstance(tools, list):
        for index, tool in enumerate(tools):
            if isinstance(tool, dict):
                name = str(tool.get("tool_name") or tool.get("name") or "").strip()
                if not name:
                    continue
                _append_tool_entity(
                    entities,
                    source_key=f"tooling.tools[{index}]",
                    name=name,
                    description=str(tool.get("tool_description") or tool.get("description") or ""),
                    raw_value=tool,
                )
            elif isinstance(tool, str) and tool.strip():
                _append_tool_entity(
                    entities,
                    source_key=f"tooling.tools[{index}]",
                    name=tool.strip(),
                    raw_value=tool,
                )

    description = str(_discovered_value(discovered, "system_profile.system_description") or "").lower()
    inferred: list[tuple[str, str]] = []
    if "crm" in description and not any(e.display_name.lower() == "crm" for e in entities if e.entity_type == "tool"):
        inferred.append(("crm", "Customer profile and CRM integration"))
    if "stock exchange" in description:
        inferred.append(("stock exchange API", "Market and stock exchange data feed"))
    if "government portal" in description:
        inferred.append(("government portal API", "Government eligibility and authentication portal"))
    if "news" in description:
        inferred.append(("news sentiment API", "News and sentiment analysis for investments"))
    for name, desc in inferred:
        _append_tool_entity(
            entities,
            source_key=f"system_profile.system_description#{name}",
            name=name,
            description=desc,
        )


def extract_from_discovery(discovered: dict[str, Any]) -> list[MappableEntity]:
    entities: list[MappableEntity] = []

    _extract_tools_from_discovered(discovered, entities)

    pii_categories = _discovered_value(discovered, "data_assets.pii_categories")
    if isinstance(pii_categories, list):
        for index, category in enumerate(pii_categories):
            key = str(category).strip()
            if not key:
                continue
            hint = PII_CATEGORY_SEARCH.get(
                key,
                (f"Personal data category: {key.replace('_', ' ')}", DATA_NODE_TYPES),
            )
            search_text, node_types = hint
            entities.append(
                MappableEntity(
                    entity_id=f"pii-{index}-{uuid4().hex[:8]}",
                    source_key=f"data_assets.pii_categories[{index}]",
                    display_name=key.replace("_", " "),
                    search_text=search_text,
                    entity_type="data_asset",
                    node_types=node_types,
                    raw_value=category,
                )
            )

    data_types = _discovered_value(discovered, "data_assets.data_types_processed")
    if isinstance(data_types, list):
        for index, data_type in enumerate(data_types):
            key = str(data_type).strip()
            if not key:
                continue
            hint = DATA_TYPE_SEARCH.get(
                key,
                (f"Financial or customer data type: {key.replace('_', ' ')}", DATA_NODE_TYPES),
            )
            search_text, node_types = hint
            entities.append(
                MappableEntity(
                    entity_id=f"data-{index}-{uuid4().hex[:8]}",
                    source_key=f"data_assets.data_types_processed[{index}]",
                    display_name=key.replace("_", " "),
                    search_text=search_text,
                    entity_type="data_asset",
                    node_types=node_types,
                    raw_value=data_type,
                )
            )

    agent_parts: list[str] = []
    for key in (
        "system_profile.business_purpose",
        "system_profile.primary_use_case",
        "system_profile.system_description",
        "system_profile.industry",
    ):
        value = _discovered_value(discovered, key)
        if isinstance(value, str) and value.strip():
            agent_parts.append(value.strip())
    if agent_parts:
        combined = ". ".join(agent_parts)
        entities.append(
            MappableEntity(
                entity_id=f"agent-{uuid4().hex[:8]}",
                source_key="system_profile.agent_profile",
                display_name=agent_parts[0][:120],
                search_text=f"AI investment and banking agent: {combined}",
                entity_type="agent",
                node_types=AGENT_NODE_TYPES,
                raw_value=combined,
            )
        )

    return entities


def extract_from_customer(record: CustomerRecord) -> list[MappableEntity]:
    entities: list[MappableEntity] = []

    for index, tool in enumerate(record.tools):
        entities.append(
            MappableEntity(
                entity_id=f"tool-{index}-{uuid4().hex[:8]}",
                source_key=f"tools[{index}]",
                display_name=tool.name,
                search_text=f"Tool: {tool.name}. {tool.description}. Category: {tool.category.value}",
                entity_type="tool",
                node_types=TOOL_NODE_TYPES,
                raw_value=tool.model_dump(),
            )
        )

    for asset in record.sensitive_data_assets:
        hint = DATA_ASSET_SEARCH_HINTS.get(
            asset.value,
            (asset.value, DATA_NODE_TYPES),
        )
        search_text, node_types = hint
        entities.append(
            MappableEntity(
                entity_id=f"asset-{uuid4().hex[:8]}",
                source_key=f"sensitive_data_assets.{asset.name}",
                display_name=asset.value,
                search_text=search_text,
                entity_type="data_asset",
                node_types=node_types,
                raw_value=asset.value,
            )
        )

    for index, asset in enumerate(record.custom_assets):
        entities.append(
            MappableEntity(
                entity_id=f"custom-{index}-{uuid4().hex[:8]}",
                source_key=f"custom_assets[{index}]",
                display_name=asset.name,
                search_text=f"Custom data asset: {asset.name}. {asset.description or ''}".strip(),
                entity_type="data_asset",
                node_types=DATA_NODE_TYPES,
                raw_value=asset.model_dump(),
            )
        )

    if record.system_information is not None:
        info = record.system_information
        entities.append(
            MappableEntity(
                entity_id=f"agent-{uuid4().hex[:8]}",
                source_key="system_information.application_name",
                display_name=info.application_name,
                search_text=(
                    f"AI agent: {info.application_name}. "
                    f"{info.application_description}. Type: {info.application_type.value}"
                ),
                entity_type="agent",
                node_types=AGENT_NODE_TYPES,
                raw_value=info.model_dump(),
            )
        )

    return entities
