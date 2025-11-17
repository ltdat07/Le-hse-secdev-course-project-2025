import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from studynotes.models import User
from studynotes.security import (
    ProblemDetailsException,
    create_access_token,
    decode_access_token,
    problem_details_exception_handler,
    require_admin,
)


def test_create_and_decode_access_token_roundtrip(monkeypatch):
    """Проверяем, что токен правильно кодируется и декодируется,
    а extra_claims попадают в payload.
    """
    monkeypatch.setenv("JWT_SECRET", "testsecret123")
    token = create_access_token(
        sub="user@example.com",
        ttl_seconds=60,
        extra_claims={"role": "user"},
        kid="kid-123",
    )
    data = decode_access_token(token)
    assert data["sub"] == "user@example.com"
    assert data["role"] == "user"


def test_create_access_token_raises_when_no_secret(monkeypatch):
    """Если JWT_SECRET не задан, должен быть RuntimeError."""
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        create_access_token("user@example.com")


def test_require_admin_allows_admin():
    """Админу доступ разрешён."""
    user = User(email="admin@example.com", role="admin")
    result = require_admin(user)
    assert result is user


def test_require_admin_rejects_non_admin():
    """Обычный пользователь получает 403."""
    user = User(email="user@example.com", role="user")
    with pytest.raises(HTTPException) as exc:
        require_admin(user)
    assert exc.value.status_code == 403


def test_problem_details_exception_handler_rfc7807_shape():
    """Проверяем, что handler выдаёт правильное тело ответа RFC7807."""
    exc = ProblemDetailsException(
        status_code=400,
        code="TEST_ERROR",
        message="Something went wrong",
        title="Test Error",
        type_="https://example.com/test-error",
        details={"foo": "bar"},
    )

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "path": "/test",
        "raw_path": b"/test",
        "query_string": b"",
        "headers": [],
        "server": ("testserver", 80),
    }
    request = Request(scope)
    response = problem_details_exception_handler(request, exc)

    assert response.status_code == 400
    data = json.loads(response.body.decode("utf-8"))
    assert data["type"] == "https://example.com/test-error"
    assert data["title"] == "Test Error"
    assert data["status"] == 400
    assert data["code"] == "TEST_ERROR"
    assert data["message"] == "Something went wrong"
    assert data["details"] == {"foo": "bar"}
    assert "correlation_id" in data