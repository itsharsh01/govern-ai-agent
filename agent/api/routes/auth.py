from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agent.api.auth_schemas import AuthUserResponse, LoginRequest, LoginResponse, RegisterRequest
from agent.api.mongo.repository import (
    ensure_default_customer,
    get_customer_by_email,
    load_customer,
    register_customer,
)
from agent.api.schemas import CustomerRecord
from agent.auth.tokens import AuthError, create_access_token, decode_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


def _user_response(record: CustomerRecord) -> AuthUserResponse:
    return AuthUserResponse(
        customer_id=record.id,
        email=str(record.email),
        name=record.name,
        company=record.company,
    )


def get_current_customer(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CustomerRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    customer_id = str(payload.get("sub", ""))
    try:
        return load_customer(customer_id)
    except HTTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found",
        ) from exc


def _registration_enabled() -> bool:
    return os.getenv("GOVERN_AUTH_ALLOW_REGISTER", "true").lower() in ("1", "true", "yes")


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest) -> LoginResponse:
    if not _registration_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled",
        )

    try:
        customer = register_customer(
            email=str(body.email),
            password=body.password,
            name=body.name,
            company=body.company,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    token = create_access_token(user_id=customer.id, email=str(customer.email))
    return LoginResponse(
        access_token=token,
        user=_user_response(customer),
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    customer = get_customer_by_email(str(body.email))
    if customer is None or not customer.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or access key",
        )

    try:
        if not verify_password(body.password, customer.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or access key",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or access key",
        ) from exc

    token = create_access_token(user_id=customer.id, email=str(customer.email))
    return LoginResponse(
        access_token=token,
        user=_user_response(customer),
    )


@router.get("/me", response_model=AuthUserResponse)
def me(current_customer: CustomerRecord = Depends(get_current_customer)) -> AuthUserResponse:
    return _user_response(current_customer)
