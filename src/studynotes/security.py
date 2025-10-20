import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

# Argon2id параметры под NFR-01
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="ID",
    argon2__rounds=3,  # ~ time_cost
    argon2__memory_cost=256 * 1024,  # 256 MB
    argon2__parallelism=1,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(
    sub: str,
    *,
    ttl_seconds: int = 900,
    extra_claims: Dict[str, Any] | None = None,
    kid: str | None = None,
) -> str:
    secret = os.getenv("JWT_SECRET", "dev_only_change_me")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        **(extra_claims or {}),
    }
    headers = {"alg": "HS256", "typ": "JWT"}
    if kid:
        headers["kid"] = kid
    return jwt.encode(payload, secret, algorithm="HS256", headers=headers)
