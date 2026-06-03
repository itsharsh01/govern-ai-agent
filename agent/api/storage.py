from __future__ import annotations

from pathlib import Path

from agent.api.mongo.repository import (
    delete_customer as mongo_delete_customer,
)
from agent.api.mongo.repository import (
    list_customers,
    load_customer,
    save_customer,
)
from agent.api.schemas import CustomerRecord

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


def ensure_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def customer_uploads_dir(customer_id: str) -> Path:
    path = UPLOADS_DIR / customer_id / "policies"
    path.mkdir(parents=True, exist_ok=True)
    return path


def discovery_uploads_dir(session_id: str) -> Path:
    path = UPLOADS_DIR / "discovery" / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path


__all__ = [
    "DATA_DIR",
    "UPLOADS_DIR",
    "CustomerRecord",
    "customer_uploads_dir",
    "delete_customer",
    "ensure_dirs",
    "list_customers",
    "load_customer",
    "save_customer",
]


def delete_customer(customer_id: str) -> bool:
    return mongo_delete_customer(customer_id)
