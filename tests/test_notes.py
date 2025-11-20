from fastapi.testclient import TestClient

from studynotes.main import app

client = TestClient(app)

EMAIL = "u1@example.com"
PASS = "password123"  # noqa: S105


def register_and_login(email=EMAIL, password=PASS):
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


def test_crud_flow():
    headers = register_and_login()

    # create tag
    r = client.post(
        "/api/v1/tags",
        headers=headers,
        json={"name": "algorithms"},
    )
    assert r.status_code == 200

    # create note
    n = {
        "title": "Dijkstra",
        "body": "Shortest path",
        "tags": ["algorithms", "graphs"],
    }
    r = client.post("/api/v1/notes", headers=headers, json=n)
    assert r.status_code == 200
    note = r.json()

    # get note
    r = client.get(f"/api/v1/notes/{note['id']}", headers=headers)
    assert r.status_code == 200

    # list by tag
    r = client.get(
        "/api/v1/notes",
        headers=headers,
        params={"tag": "algorithms"},
    )
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # patch
    r = client.patch(
        f"/api/v1/notes/{note['id']}",
        headers=headers,
        json={"title": "Dijkstra algo"},
    )
    assert r.status_code == 200

    # delete
    r = client.delete(f"/api/v1/notes/{note['id']}", headers=headers)
    assert r.status_code == 204
