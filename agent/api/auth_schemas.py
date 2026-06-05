from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)


class AuthUserResponse(BaseModel):
    customer_id: str
    email: str
    name: str
    company: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86_400
    user: AuthUserResponse
