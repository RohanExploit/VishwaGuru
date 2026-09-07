"""Rate limiting must actually be enforced.

RATE_LIMIT_ENABLED and MAX_REQUESTS_PER_MINUTE were declared in render.yaml and
parsed in backend/config.py, but no middleware ever read them, so every endpoint
was unmetered. The detector routes call paid inference APIs on each request, so
that was a billing exposure as much as an availability one. These tests fail if
the enforcement is removed again.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import backend.main as main_module
from backend.main import app


@pytest.fixture(autouse=True)
def reset_limiter():
    """slowapi keeps counters in process, so they must not leak between tests."""
    main_module.limiter.reset()
    yield
    main_module.limiter.reset()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (90, 90, 90)).save(buf, format="JPEG")
    return buf.getvalue()


def test_limiter_is_enabled_by_default():
    assert main_module.limiter.enabled
    assert main_module.AI_REQUESTS_PER_MINUTE < main_module.MAX_REQUESTS_PER_MINUTE, (
        "AI-backed routes should be metered more tightly than plain reads."
    )


def test_health_is_never_throttled(client):
    """The platform restarts a service whose health check starts failing."""
    for _ in range(main_module.MAX_REQUESTS_PER_MINUTE + 5):
        assert client.get("/health").status_code == 200


def test_ai_endpoint_is_throttled(client, jpeg, monkeypatch):
    async def _stub(*_args, **_kwargs):
        return []

    monkeypatch.setattr(main_module, "detect_fire_clip", _stub, raising=False)

    limit = main_module.AI_REQUESTS_PER_MINUTE
    statuses = [
        client.post(
            "/api/detect-fire",
            files={"image": ("f.jpg", jpeg, "image/jpeg")},
        ).status_code
        for _ in range(limit + 2)
    ]

    assert 429 in statuses, f"Expected a 429 after {limit} requests in a minute, got {statuses}"
    assert statuses[0] != 429, "The first request should not be rejected."
