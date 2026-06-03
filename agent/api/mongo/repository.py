from __future__ import annotations

from fastapi import HTTPException, status

from agent.api.schemas import CustomerRecord

from .client import get_customers_collection


def save_customer(record: CustomerRecord) -> CustomerRecord:
    collection = get_customers_collection()
    doc = record.model_dump(mode="json")
    collection.replace_one({"id": record.id}, doc, upsert=True)
    return record


def load_customer(customer_id: str) -> CustomerRecord:
    collection = get_customers_collection()
    doc = collection.find_one({"id": customer_id})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found",
        )
    doc.pop("_id", None)
    return CustomerRecord.model_validate(doc)


def list_customers() -> list[CustomerRecord]:
    collection = get_customers_collection()
    records: list[CustomerRecord] = []
    for doc in collection.find().sort("created_at", -1):
        doc.pop("_id", None)
        records.append(CustomerRecord.model_validate(doc))
    return records


def delete_customer(customer_id: str) -> bool:
    collection = get_customers_collection()
    result = collection.delete_one({"id": customer_id})
    return result.deleted_count > 0
