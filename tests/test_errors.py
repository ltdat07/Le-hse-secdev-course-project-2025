from fastapi.testclient import TestClient

from studynotes.main import app

client = TestClient(app)


def test_rfc7807_not_found():
    r = client.get("/__nope__")
    assert r.status_code == 404
    body = r.json()
    for k in (
        "type",
        "title",
        "status",
        "detail",
        "correlation_id",
        "code",
        "message",
        "details",
    ):
        assert k in body
    assert body["code"] == "HTTP_ERROR"


def test_rfc7807_validation_error():
    r = client.post("/validate", json={"name": ""})
    assert r.status_code == 422
    body = r.json()
    for k in (
        "type",
        "title",
        "status",
        "detail",
        "correlation_id",
        "code",
        "message",
        "details",
    ):
        assert k in body
    assert body["code"] == "VALIDATION_ERROR"
