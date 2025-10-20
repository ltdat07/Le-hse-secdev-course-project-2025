from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def problem(
    status: int,
    title: str,
    detail: str,
    code: str = "ERROR",
    details: dict | None = None,
):
    cid = str(uuid4())
    return JSONResponse(
        {
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "correlation_id": cid,
            "code": code,
            "message": detail,
            "details": details or {},
        },
        status_code=status,
        media_type="application/problem+json",
    )


def make_exception_handlers():
    async def http_exc_handler(request: Request, exc: StarletteHTTPException):
        return problem(
            exc.status_code,
            exc.detail or "HTTP error",
            exc.detail or "",
            code="HTTP_ERROR",
        )

    async def not_found_handler(request: Request, exc):
        return problem(404, "Not Found", "Not Found", code="HTTP_ERROR")

    async def validation_exc_handler(request: Request, exc: RequestValidationError):
        return problem(
            422,
            "Validation error",
            "Invalid request",
            code="VALIDATION_ERROR",
            details={"errors": exc.errors()},
        )

    async def unhandled_exc_handler(request: Request, exc: Exception):
        return problem(
            500, "Internal error", "Something went wrong", code="INTERNAL_ERROR"
        )

    return {
        StarletteHTTPException: http_exc_handler,
        404: not_found_handler,
        RequestValidationError: validation_exc_handler,
        Exception: unhandled_exc_handler,
    }
