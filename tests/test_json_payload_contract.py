"""The JSON bodies the frontend actually sends must be accepted.

tests/test_api_contract.py proves a path exists and accepts the right upload
field. It cannot see JSON request bodies, and that blind spot hid two live
failures that reached users:

  ReportForm.jsx posts {"description": ...} to /api/analyze-urgency, which
  required "text"                                                       -> 422
  ChatWidget.jsx posts {"query": ...} to /api/chat, which required
  "message"                                                             -> 422

Both looked healthy to a path-only check: the route existed, the method was
right, and the frontend swallowed the error into a console.error, so the
feature just silently never worked.

Each case below is the exact body the corresponding component sends.
"""

import pytest
from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def stub_models(monkeypatch):
    """Keep these tests about the request contract, not the model backends."""

    async def _urgency(*_args, **_kwargs):
        return {"urgency": "High", "score": 0.9}

    async def _chat(*_args, **_kwargs):
        return "A civic assistant reply."

    monkeypatch.setattr(main_module, "analyze_urgency_text", _urgency, raising=False)
    monkeypatch.setattr(main_module, "chat_with_civic_assistant", _chat, raising=False)


# (path, body, the component that sends exactly this)
FRONTEND_JSON_BODIES = [
    ("/api/analyze-urgency", {"description": "Large pothole near the school gate"}, "views/ReportForm.jsx"),
    ("/api/chat", {"query": "Who fixes broken streetlights?"}, "components/ChatWidget.jsx"),
    ("/api/mh/rep-contacts", {"pincode": "411001"}, "api/location.js"),
]


@pytest.mark.parametrize("path,body,source", FRONTEND_JSON_BODIES)
def test_frontend_json_body_is_accepted(client, path, body, source):
    response = client.post(path, json=body)
    assert response.status_code != 422, (
        f"{path} rejected the body {source} actually sends: {body}\n"
        f"Response: {response.text[:300]}"
    )


# Canonical field names must keep working alongside the aliases.
CANONICAL_JSON_BODIES = [
    ("/api/analyze-urgency", {"text": "Large pothole near the school gate"}),
    ("/api/chat", {"message": "Who fixes broken streetlights?"}),
]


@pytest.mark.parametrize("path,body", CANONICAL_JSON_BODIES)
def test_canonical_field_still_accepted(client, path, body):
    response = client.post(path, json=body)
    assert response.status_code != 422, f"{path} stopped accepting its canonical field: {body}"


@pytest.mark.parametrize("path", ["/api/analyze-urgency", "/api/chat"])
def test_empty_body_is_rejected(client, path):
    """Accepting both names must not mean accepting neither."""
    assert client.post(path, json={}).status_code == 422


@pytest.mark.parametrize("path", ["/api/analyze-urgency", "/api/chat"])
def test_blank_string_is_rejected(client, path):
    """Whitespace is not content; sending it to a paid model would just burn quota."""
    for body in ({"text": "   "}, {"description": "   "}, {"message": "   "}, {"query": "   "}):
        response = client.post(path, json=body)
        assert response.status_code == 422, (
            f"{path} accepted a blank value {body} instead of rejecting it."
        )
