from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from agent.api.main import app
from agent.api.schemas import CustomerRecord
from agent.auth.tokens import hash_password


DEMO_CUSTOMER = CustomerRecord(
    id="cust-1",
    name="Root Operator",
    email="root@gov.os",
    company="GovernAI Demo",
    password_hash=hash_password("governai-dev"),
)


@pytest.fixture
def client():
    return TestClient(app)


@patch("agent.api.routes.auth.get_customer_by_email", return_value=DEMO_CUSTOMER)
def test_login_success(_mock_get, client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "root@gov.os", "password": "governai-dev"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["customer_id"] == "cust-1"
    assert body["user"]["email"] == "root@gov.os"


@patch("agent.api.routes.auth.get_customer_by_email", return_value=DEMO_CUSTOMER)
def test_login_invalid_password(_mock_get, client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "root@gov.os", "password": "wrong-key"},
    )
    assert res.status_code == 401


@patch("agent.api.routes.auth.load_customer", return_value=DEMO_CUSTOMER)
@patch("agent.api.routes.auth.get_customer_by_email", return_value=DEMO_CUSTOMER)
def test_me_requires_bearer(_mock_get, _mock_load, client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "root@gov.os", "password": "governai-dev"},
    )
    token = login.json()["access_token"]

    ok = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["customer_id"] == "cust-1"

    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401


@patch("agent.api.routes.auth.register_customer")
@patch("agent.api.routes.auth.get_customer_by_email", return_value=None)
def test_register_success(_mock_get, mock_register, client):
    mock_register.return_value = CustomerRecord(
        id="cust-2",
        name="Ops User",
        email="ops@example.com",
        company="Acme",
        password_hash=hash_password("secure-pass-1"),
    )
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ops@example.com",
            "password": "secure-pass-1",
            "name": "Ops User",
            "company": "Acme",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["user"]["customer_id"] == "cust-2"


@patch("agent.api.routes.auth.register_customer", side_effect=ValueError("Email already registered"))
def test_register_duplicate_email(mock_register, client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "root@gov.os", "password": "secure-pass-1"},
    )
    assert res.status_code == 409


def test_register_password_too_short(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "short"},
    )
    assert res.status_code == 422
