"""Privileged endpoints must not be callable without a key.

Before this, every endpoint in the service was public, including the two that
change state officials act on: escalating a grievance reassigns it to a
different authority and writes an audit record, and verifying an issue changes
the status the public dashboard reports.
"""

import io

import jwt
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.auth import (
    ADMIN_API_KEY_ENV,
    JWT_ALGORITHM,
    JWT_SECRET_ENV,
    MIN_API_KEY_LENGTH,
)
from backend.main import app

VALID_KEY = "k" * MIN_API_KEY_LENGTH
JWT_SECRET = "s" * 40

PROTECTED = (
    "/api/issues/1/verify",
    "/api/grievances/1/escalate",
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (100, 100, 100)).save(buf, format="JPEG")
    return buf.getvalue()


def _call(client, path, jpeg=None, headers=None):
    if path.endswith("/verify"):
        return client.post(
            path, files={"image": ("f.jpg", jpeg, "image/jpeg")}, headers=headers or {}
        )
    return client.post(path, headers=headers or {})


@pytest.mark.parametrize("path", PROTECTED)
def test_missing_key_is_rejected(client, jpeg, path, monkeypatch):
    monkeypatch.setenv(ADMIN_API_KEY_ENV, VALID_KEY)
    response = _call(client, path, jpeg)
    assert response.status_code == 401, f"{path} accepted a request with no X-API-Key header."


@pytest.mark.parametrize("path", PROTECTED)
def test_wrong_key_is_rejected(client, jpeg, path, monkeypatch):
    monkeypatch.setenv(ADMIN_API_KEY_ENV, VALID_KEY)
    response = _call(client, path, jpeg, headers={"X-API-Key": "n" * MIN_API_KEY_LENGTH})
    assert response.status_code == 401, f"{path} accepted an incorrect key."


@pytest.mark.parametrize("path", PROTECTED)
def test_unset_key_fails_closed(client, jpeg, path, monkeypatch):
    """An unset secret must not read as 'no authentication required'."""
    monkeypatch.delenv(ADMIN_API_KEY_ENV, raising=False)
    response = _call(client, path, jpeg, headers={"X-API-Key": VALID_KEY})
    assert response.status_code == 503, (
        f"{path} did not fail closed when {ADMIN_API_KEY_ENV} was unset "
        f"(got {response.status_code})."
    )


@pytest.mark.parametrize("path", PROTECTED)
def test_weak_key_is_refused(client, jpeg, path, monkeypatch):
    """A short key is a placeholder, and accepting it would only look like security."""
    monkeypatch.setenv(ADMIN_API_KEY_ENV, "short")
    response = _call(client, path, jpeg, headers={"X-API-Key": "short"})
    assert response.status_code == 503, f"{path} accepted a key below the minimum length."


@pytest.mark.parametrize("path", PROTECTED)
def test_correct_key_passes_the_auth_layer(client, jpeg, path, monkeypatch):
    """The request may still 404 on a missing row -- it must not 401 or 503."""
    monkeypatch.setenv(ADMIN_API_KEY_ENV, VALID_KEY)
    response = _call(client, path, jpeg, headers={"X-API-Key": VALID_KEY})
    assert response.status_code not in (401, 503), (
        f"{path} rejected a correct key with {response.status_code}."
    )


def test_public_endpoints_stay_public(client):
    """Anonymous reporting is a feature; the guard must not have leaked onto reads."""
    for path in ("/health", "/api/stats", "/api/issues/recent", "/api/grievances"):
        assert client.get(path).status_code == 200, f"{path} stopped being public."


# --- bearer token identity -------------------------------------------------


def test_no_token_is_anonymous():
    from backend.auth import optional_user

    assert optional_user(authorization=None) is None


def test_malformed_authorization_header_is_rejected():
    from fastapi import HTTPException

    from backend.auth import optional_user

    with pytest.raises(HTTPException) as exc:
        optional_user(authorization="Token abc123")
    assert exc.value.status_code == 401


def test_valid_token_yields_identity(monkeypatch):
    from backend.auth import optional_user

    monkeypatch.setenv(JWT_SECRET_ENV, JWT_SECRET)
    token = jwt.encode(
        {"sub": "user-42", "email": "citizen@example.com"}, JWT_SECRET, algorithm=JWT_ALGORITHM
    )

    user = optional_user(authorization=f"Bearer {token}")
    assert user is not None
    assert user.email == "citizen@example.com"
    assert user.subject == "user-42"


def test_token_signed_with_another_key_is_rejected(monkeypatch):
    """A bad token must 401, not silently degrade to anonymous."""
    from fastapi import HTTPException

    from backend.auth import optional_user

    monkeypatch.setenv(JWT_SECRET_ENV, JWT_SECRET)
    forged = jwt.encode({"sub": "attacker"}, "a-different-secret", algorithm=JWT_ALGORITHM)

    with pytest.raises(HTTPException) as exc:
        optional_user(authorization=f"Bearer {forged}")
    assert exc.value.status_code == 401


def test_unsigned_token_is_rejected(monkeypatch):
    """`alg: none` must never be accepted."""
    from fastapi import HTTPException

    from backend.auth import optional_user

    monkeypatch.setenv(JWT_SECRET_ENV, JWT_SECRET)
    unsigned = jwt.encode({"sub": "attacker"}, key="", algorithm="none")

    with pytest.raises(HTTPException) as exc:
        optional_user(authorization=f"Bearer {unsigned}")
    assert exc.value.status_code == 401
