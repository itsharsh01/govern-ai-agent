"""Normalized discovery tokens → ontology node name keys (for exact match)."""

from __future__ import annotations

# Keys are normalized via search.normalize_name before lookup.
ONTOLOGY_NAME_ALIASES: dict[str, str] = {
    "crm": "crm tool",
    "email": "customer email",
    "phone": "phone number",
    "bank account": "account number",
    "card number": "payment card data pan cvv",
    "credit score": "credit score risk profile",
    "name": "customer pii",
    "national id": "customer pii",
    "address": "customer pii",
    "customer pii": "customer pii",
    "transaction history": "account balance transaction history",
    "financial data": "account balance transaction history",
    "credit data": "credit score risk profile",
    "kyc documents": "kyc documents",
    "investment portfolio": "investment portfolio holdings",
    "account data": "account balance transaction history",
    "employment data": "customer pii",
    "market data": "investment portfolio holdings",
    "internal documents": "kyc documents",
    "financial analysis agent": "investment assistant agent",
    "financial portfolio optimizer": "investment assistant agent",
    "investment": "investment assistant agent",
    "stock exchange": "portfolio management api",
    "government portal": "regulatory reporting api",
    "news websites": "portfolio management api",
}
