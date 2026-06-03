from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from agent.api.schemas import (
    ApplicationType,
    CustomerCreate,
    CustomerResponse,
    CustomerRecord,
    DataAssetsUpdate,
    MessageResponse,
    PolicyFileRecord,
    PolicyType,
    SystemInformationRecord,
    SystemInformationUpdate,
    ToolCreate,
    ToolRecord,
    ToolsReplace,
)
from agent.api.storage import (
    DATA_DIR,
    customer_uploads_dir,
    list_customers,
    load_customer,
    save_customer,
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(body: CustomerCreate) -> CustomerResponse:
    record = CustomerRecord(
        name=body.name,
        email=body.email,
        company=body.company,
    )
    save_customer(record)
    return CustomerResponse.from_record(record)


@router.get("", response_model=list[CustomerResponse])
def get_all_customers() -> list[CustomerResponse]:
    return [CustomerResponse.from_record(c) for c in list_customers()]


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str) -> CustomerResponse:
    return CustomerResponse.from_record(load_customer(customer_id))


# --- Step 1: System Information ---


@router.put("/{customer_id}/system-information", response_model=CustomerResponse)
def update_system_information(
    customer_id: str,
    body: SystemInformationUpdate,
) -> CustomerResponse:
    if body.application_type == ApplicationType.CUSTOM and not body.custom_application_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="custom_application_type is required when application_type is Custom",
        )

    record = load_customer(customer_id)
    record.system_information = SystemInformationRecord(
        **body.model_dump(),
        updated_at=datetime.now(timezone.utc),
    )
    save_customer(record)
    return CustomerResponse.from_record(record)


# --- Step 2: Tools & Integrations ---


@router.get("/{customer_id}/tools", response_model=list[ToolRecord])
def list_tools(customer_id: str) -> list[ToolRecord]:
    return load_customer(customer_id).tools


@router.post("/{customer_id}/tools", response_model=ToolRecord, status_code=status.HTTP_201_CREATED)
def add_tool(customer_id: str, body: ToolCreate) -> ToolRecord:
    record = load_customer(customer_id)
    tool = ToolRecord(**body.model_dump())
    record.tools.append(tool)
    save_customer(record)
    return tool


@router.put("/{customer_id}/tools", response_model=CustomerResponse)
def replace_tools(customer_id: str, body: ToolsReplace) -> CustomerResponse:
    record = load_customer(customer_id)
    record.tools = [ToolRecord(**t.model_dump()) for t in body.tools]
    save_customer(record)
    return CustomerResponse.from_record(record)


@router.delete("/{customer_id}/tools/{tool_id}", response_model=MessageResponse)
def delete_tool(customer_id: str, tool_id: str) -> MessageResponse:
    record = load_customer(customer_id)
    before = len(record.tools)
    record.tools = [t for t in record.tools if t.id != tool_id]
    if len(record.tools) == before:
        raise HTTPException(status_code=404, detail="Tool not found")
    save_customer(record)
    return MessageResponse(message="Tool deleted", customer_id=customer_id)


# --- Step 3: Data Assets ---


@router.put("/{customer_id}/data-assets", response_model=CustomerResponse)
def update_data_assets(customer_id: str, body: DataAssetsUpdate) -> CustomerResponse:
    from agent.api.schemas import CustomAssetRecord

    record = load_customer(customer_id)
    record.sensitive_data_assets = body.sensitive_data_assets
    record.custom_assets = [
        CustomAssetRecord(**a.model_dump()) for a in body.custom_assets
    ]
    save_customer(record)
    return CustomerResponse.from_record(record)


# --- Step 3: Policy PDF uploads ---


@router.post("/{customer_id}/policies/{policy_type}", response_model=PolicyFileRecord)
async def upload_policy(
    customer_id: str,
    policy_type: PolicyType,
    file: UploadFile = File(...),
) -> PolicyFileRecord:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    record = load_customer(customer_id)
    upload_dir = customer_uploads_dir(customer_id)
    safe_name = f"{policy_type.value}_{file.filename.replace(' ', '_')}"
    dest: Path = upload_dir / safe_name

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be under 20MB")
    dest.write_bytes(content)

    policy = PolicyFileRecord(
        policy_type=policy_type,
        filename=file.filename,
        stored_path=str(dest.relative_to(DATA_DIR)),
        uploaded_at=datetime.now(timezone.utc),
    )
    record.policies = [p for p in record.policies if p.policy_type != policy_type]
    record.policies.append(policy)
    save_customer(record)
    return policy


@router.get("/{customer_id}/policies", response_model=list[PolicyFileRecord])
def list_policies(customer_id: str) -> list[PolicyFileRecord]:
    return load_customer(customer_id).policies
