"""Contract tests: what the frontend calls must exist, and must actually work.

This guards the failure that shipped to production: the frontend called 18
detector endpoints while backend/main.py defined 5, so 15 of them returned 404
to real users and nothing in the repository noticed.

The frontend source is scanned directly rather than compared against a
hand-maintained list, so the check cannot drift away from what the app really
requests. Three separate classes of breakage are covered:

  1. the path is not declared at all                -> 404
  2. the path is declared but not for that method   -> 405
  3. the path and method exist but the upload field
     name disagrees with the caller                 -> 422

All three had live instances in this codebase.
"""

import io
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

INTERPOLATION_RE = re.compile(r"\$\{[^}]*\}")

# Any '/api/...' occurrence is collected, regardless of what precedes it. An
# earlier version required the path to sit immediately after a quote or
# backtick, which made the dominant call pattern in this codebase --
# fetch(`${API_URL}/api/detect-fire`) -- invisible to the scan, and hid four
# endpoints that had no backend implementation at all.
#
# The lookbehind rejects relative module specifiers such as
# `import { detectorsApi } from './api/detectors'`, which are not HTTP calls.
API_PATH_RE = re.compile(r"(?<![.\w])/api/[A-Za-z0-9/_.\-${}]*")

IGNORED = {"/api"}


def _normalise(raw: str) -> str:
    """Collapse interpolations to a placeholder segment, drop any query string."""
    path = INTERPOLATION_RE.sub("1", raw)
    path = path.split("?", 1)[0]
    path = path.rstrip(".,;:)")
    return path.rstrip("/") or "/"


def _frontend_api_paths() -> set[str]:
    paths: set[str] = set()
    for path in FRONTEND_SRC.rglob("*.js*"):
        if "__tests__" in path.parts or "__mocks__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for raw in API_PATH_RE.findall(text):
            normalised = _normalise(raw)
            if normalised not in IGNORED and normalised.startswith("/api/"):
                paths.add(normalised)
    return paths


def _openapi_paths() -> dict[str, set[str]]:
    """Declared paths mapped to their HTTP methods.

    The OpenAPI schema is used rather than app.routes because
    app.include_router() inserts a wrapper object with no `.path` of its own,
    so a flat scan of app.routes silently skips every route from a mounted
    router -- which reported the whole grievance feature as missing.
    """
    schema = app.openapi()
    return {
        path: {method.upper() for method in operations}
        for path, operations in schema["paths"].items()
    }


def _matches(called: str, declared: dict[str, set[str]]) -> str | None:
    """Return the declared template matching `called`, or None.

    A literal segment in the template must match exactly; only `{param}`
    segments are treated as wildcards.
    """
    if called in declared:
        return called
    called_parts = called.strip("/").split("/")
    for template in declared:
        template_parts = template.strip("/").split("/")
        if len(template_parts) != len(called_parts):
            continue
        if all(
            (t.startswith("{") and t.endswith("}") and c) or t == c
            for t, c in zip(template_parts, called_parts, strict=True)
        ):
            return template
    return None


def test_frontend_scan_finds_endpoints():
    """Guard the guard: if the scan returns nothing, everything below is vacuous."""
    found = _frontend_api_paths()
    assert len(found) > 30, f"Frontend scan collapsed to {len(found)} paths"


@pytest.mark.parametrize("called", sorted(_frontend_api_paths()))
def test_frontend_endpoint_exists_in_backend(called):
    declared = _openapi_paths()
    assert _matches(called, declared) is not None, (
        f"The frontend calls {called} but the backend declares no such route. "
        f"Users hitting this feature get a 404."
    )


def test_no_duplicate_route_paths():
    """FastAPI serves the first match, so a duplicate silently disables the later handler."""
    seen: dict[tuple[str, str], int] = {}
    for route in app.routes:
        for method in getattr(route, "methods", set()) or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            key = (method, getattr(route, "path", None))
            if key[1] is None:
                continue
            seen[key] = seen.get(key, 0) + 1
    duplicates = {k: v for k, v in seen.items() if v > 1}
    assert not duplicates, f"Duplicate route registrations shadow later handlers: {duplicates}"


def _detector_paths() -> list[str]:
    return sorted(p for p in _openapi_paths() if p.startswith("/api/detect-"))


@pytest.mark.parametrize("path", _detector_paths())
def test_detector_routes_accept_post(path):
    assert "POST" in _openapi_paths()[path], (
        f"{path} is declared but not for POST; every frontend detector call posts."
    )


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (110, 110, 110)).save(buf, format="JPEG")
    return buf.getvalue()


# Detector endpoints whose upload field is `file` rather than `image`, because
# the callers post a recorded audio blob.
AUDIO_FIELD_PATHS = {"/api/detect-audio", "/api/transcribe-audio"}


@pytest.mark.parametrize("path", _detector_paths())
def test_detector_routes_accept_the_field_name_callers_send(path, monkeypatch):
    """A declared route is not a working route.

    Four handlers named their upload `file` while all 25 frontend call sites
    posted `image`, so they answered 422 on every request while looking
    perfectly healthy to a path-only check.
    """
    import backend.main as main_module

    async def _stub(*_args, **_kwargs):
        return []

    for name in {service for _, service, _ in main_module.DETECTOR_ENDPOINTS}:
        monkeypatch.setattr(main_module, name, _stub, raising=False)
    for name in ("detect_infrastructure_local", "detect_audio_event", "transcribe_audio"):
        monkeypatch.setattr(main_module, name, _stub, raising=False)

    field = "file" if path in AUDIO_FIELD_PATHS else "image"
    payload = b"fake-audio" if field == "file" else _jpeg()

    with TestClient(app) as client:
        response = client.post(
            path, files={field: ("upload.bin", payload, "application/octet-stream")}
        )

    assert response.status_code != 422, (
        f"{path} rejected a `{field}` upload with 422. The handler's parameter name "
        f"disagrees with what the frontend posts."
    )
    assert response.status_code != 405, f"{path} does not accept POST."
