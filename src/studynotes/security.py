import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

# Секрет читаем из ENV, чтобы тесты могли monkeypatch'ить JWT_SECRET
SECRET = os.getenv("JWT_SECRET", "change-me")
ALGO = "HS256"

# Argon2 (мягко: t=3, m=262144, p=1 — под тесты вида $argon2id$v=19$m=262144,t=3,p=1$...)
pwd_ctx = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=262_144,  # KiB
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
    extra_claims: Optional[Dict[str, Any]] = None,
    kid: Optional[str] = None,
) -> str:
    """
    Делает JWT с настраиваемым TTL, доп. полями и заголовком kid (под тесты).
    """
    now = datetime.now(tz=timezone.utc)
    claims: Dict[str, Any] = {"sub": sub, "iat": now, "exp": now + timedelta(seconds=ttl_seconds)}
    if extra_claims:
        claims.update(extra_claims)

    headers = {"typ": "JWT", "alg": ALGO}
    if kid:
        headers["kid"] = kid

    secret = os.getenv("JWT_SECRET", SECRET)
    return jwt.encode(claims, secret, algorithm=ALGO, headers=headers)


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message": "Invalid or missing token", "details": {}},
    )
    try:
        secret = os.getenv("JWT_SECRET", SECRET)
        payload = jwt.decode(token, secret, algorithms=[ALGO])
        email: str = payload.get("sub")  # в нашем токене sub = email
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc
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
