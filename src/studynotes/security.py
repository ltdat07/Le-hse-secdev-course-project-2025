import os
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET = os.getenv("JWT_SECRET", "change-me")
ALGO = "HS256"

pwd_ctx = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=262_144,
    argon2__parallelism=1,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)


def create_access_token(
    sub: str,
    ttl_seconds: int = 60 * 60,
    extra_claims: dict[str, Any] | None = None,
    kid: str | None = None,
) -> str:
    now = datetime.now(tz=UTC)
    claims: dict[str, Any] = {
        "sub": sub,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    if extra_claims:
        claims.update(extra_claims)

    headers = {"typ": "JWT", "alg": ALGO}
    if kid:
        headers["kid"] = kid

    secret = os.getenv("JWT_SECRET", SECRET)
    return jwt.encode(claims, secret, algorithm=ALGO, headers=headers)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "UNAUTHORIZED",
            "message": "Invalid or missing token",
            "details": {},
        },
    )
    try:
        secret = os.getenv("JWT_SECRET", SECRET)
        payload = jwt.decode(token, secret, algorithms=[ALGO])
        email: str | None = payload.get("sub")
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc from None
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise cred_exc
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Admin only", "details": {}},
        )
    return user