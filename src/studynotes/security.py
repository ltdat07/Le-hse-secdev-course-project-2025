import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

MIN_JWT_SECRET_LENGTH = 8

_pwd_ctx = CryptContext(
    schemes=["argon2"],
    default="argon2",
    deprecated="auto",
    argon2__memory_cost=262_144,
    argon2__time_cost=3,
    argon2__parallelism=1,
)


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _pwd_ctx.verify(password, hashed)


ALGORITHM = "HS256"
DEFAULT_TTL_SECONDS = 60 * 60


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:

        raise RuntimeError("JWT_SECRET environment variable must be set")

    if len(secret) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET is too short (len={len(secret)}), "
            f"must be at least {MIN_JWT_SECRET_LENGTH} characters"
        )

    return secret


def create_access_token(
    sub: str,
    ttl_seconds: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
    kid: Optional[str] = None,
) -> str:
    now = datetime.now(timezone.utc)
    ttl = ttl_seconds or DEFAULT_TTL_SECONDS

    payload: Dict[str, Any] = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    headers: Dict[str, Any] = {}
    if kid is not None:
        headers["kid"] = kid

    token = jwt.encode(
        payload,
        _get_jwt_secret(),
        algorithm=ALGORITHM,
        headers=headers or None,
    )
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _get_jwt_secret(), algorithms=[ALGORITHM])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise cred_exc

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Admin only",
                "details": {},
            },
        )
    return user


class ProblemDetailsException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        title: Optional[str] = None,
        type_: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.title = title or message
        self.type_ = type_ or "about:blank"
        self.details = details or {}


def problem_details_exception_handler(
    request: Request,
    exc: ProblemDetailsException,
) -> JSONResponse:
    correlation_id = str(uuid4())
    body = {
        "type": exc.type_,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.message,
        "instance": str(request.url),
        "correlation_id": correlation_id,
        "code": exc.code,
        "message": exc.message,
        "details": exc.details,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        media_type="application/problem+json",
    )
