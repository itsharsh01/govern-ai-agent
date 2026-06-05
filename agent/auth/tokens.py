from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any


class AuthError(Exception):
    pass


def _secret() -> str:
    return os.getenv("GOVERN_AUTH_SECRET", "governai-dev-secret-change-me")


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError as exc:
        raise AuthError("Invalid stored password hash") from exc
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(actual, expected)


def create_access_token(*, user_id: str, email: str, ttl_seconds: int = 86_400) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + ttl_seconds,
    }
    body = urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise AuthError("Malformed token") from exc

    expected = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise AuthError("Invalid token signature")

    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(urlsafe_b64decode(padded.encode()).decode())
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthError("Token expired")
    return payload
