from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from studynotes.main import app

client = TestClient(app)


def register_and_login(email: str) -> dict:
    password = "Password123"

    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code in (200, 400)

    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200

    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_short_password_rejected():
    r = client.post(
        "/api/v1/auth/register",
        json={"email": f"{uuid4()}@example.com", "password": "short"},
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["status"] == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert "password" in str(body["details"]).lower()


def test_create_note_rejects_extra_field():
    headers = register_and_login("extra-field@example.com")

    r = client.post(
        "/api/v1/notes",
        json={
            "title": "Valid title",
            "body": "Valid body",
            "tags": [],
            "evil": "field",
        },
        headers=headers,
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["status"] == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert "extra" in str(body["details"]).lower() or "unexpected" in str(body["details"]).lower()


def test_get_nonexistent_note_rfc7807():
    headers = register_and_login("missing-note@example.com")

    r = client.get("/api/v1/notes/999999", headers=headers)
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")

    body = r.json()
    for key in (
        "type",
        "title",
        "status",
        "detail",
        "correlation_id",
        "code",
        "message",
        "details",
    ):
        assert key in body

    assert body["code"] == "NOT_FOUND"


def test_search_note_sql_injection_safe():
    headers = register_and_login("sqlinj@example.com")

    create_resp = client.post(
        "/api/v1/notes",
        json={"title": "Safe title", "body": "Safe body", "tags": []},
        headers=headers,
    )
    assert create_resp.status_code == 200

    injection = "'; DROP TABLE notes;--"
    r = client.get("/api/v1/notes", params={"q": injection}, headers=headers)
    assert r.status_code == 200

    r2 = client.get("/api/v1/notes", headers=headers)
    assert r2.status_code == 200

    items = r2.json()
    assert isinstance(items, list)
    assert any(note["title"] == "Safe title" for note in items)


def test_jwt_secret_too_short(monkeypatch):
    from studynotes.security import create_access_token

    monkeypatch.setenv("JWT_SECRET", "short")

    with pytest.raises(RuntimeError):
        create_access_token("user-1", ttl_seconds=60, extra_claims={"role": "user"})
