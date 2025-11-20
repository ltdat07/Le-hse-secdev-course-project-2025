from jose import jwt

from studynotes.security import (create_access_token, hash_password,
                                 verify_password)


def test_argon2_hash_and_verify_ok():
    h = hash_password("S3curePa$$")
    assert h.startswith("$argon2id$")
    assert verify_password("S3curePa$$", h)
    assert not verify_password("wrong", h)


def test_argon2_params_match_nfr_via_hash():
    h = hash_password("check-params")
    parts = h.split("$")
    params = parts[3]
    kv = dict(p.split("=") for p in params.split(","))
    m = int(kv["m"])
    t = int(kv["t"])
    p = int(kv["p"])
    assert m >= 256 * 1024
    assert t >= 3
    assert p == 1


def test_jwt_created_and_decodable(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test_secret_123")
    token = create_access_token(
        "user-1", ttl_seconds=60, extra_claims={"role": "user"}, kid="kid-1"
    )
    header = jwt.get_unverified_header(token)
    claims = jwt.get_unverified_claims(token)
    assert header.get("kid") == "kid-1"
    assert claims["sub"] == "user-1"
    assert "exp" in claims and "iat" in claims
