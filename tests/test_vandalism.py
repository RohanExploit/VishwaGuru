"""Tests for the vandalism detection endpoint.

Rewritten: the previous version declared four @patch decorators but only three
parameters, and patched `backend.main.magic` / `backend.main.detect_vandalism_local`
-- neither of which exists on the current module. It could never run.
"""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (120, 120, 120)).save(buf, format="JPEG")
    return buf.getvalue()


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert body["data"]["service"] == "VishwaGuru API"


def test_detect_vandalism_returns_detections(client, jpeg_bytes, monkeypatch):
    expected = [{"label": "graffiti", "confidence": 0.95, "box": []}]
    monkeypatch.setattr("backend.main.detect_vandalism", lambda img: expected)

    response = client.post(
        "/api/detect-vandalism",
        files={"image": ("frame.jpg", jpeg_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {"detections": expected}


def test_detect_vandalism_accepts_image_field_not_file(client, jpeg_bytes, monkeypatch):
    """Every frontend caller posts the field as `image`; `file` must not be required."""
    monkeypatch.setattr("backend.main.detect_vandalism", lambda img: [])

    response = client.post(
        "/api/detect-vandalism",
        files={"image": ("frame.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert response.status_code == 200


def test_detect_vandalism_rejects_missing_image(client):
    response = client.post("/api/detect-vandalism")
    assert response.status_code == 422
