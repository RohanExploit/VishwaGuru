"""Contract test: every endpoint the frontend calls must exist in the backend.

This is the guard for the failure that shipped to production: the frontend
called 18 detector endpoints while backend/main.py defined 5, so 15 of them
returned 404 to real users and nothing in the repository noticed.

The frontend source is scanned directly rather than a hand-maintained list, so
the check cannot drift away from what the app actually requests.
"""
import re
from pathlib import Path

import pytest

from backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

# Template-literal interpolations are collapsed to a single path segment before
# matching. An earlier version of this regex only accepted [A-Za-z0-9/_-], so
# `/api/issues/${id}/vote` was skipped entirely -- and that call really was
# broken, because the backend serves /upvote. Any path built by interpolation
# must be checked, not ignored.
INTERPOLATION_RE = re.compile(r"\$\{[^}]*\}")
API_PATH_RE = re.compile(r"""['"`](/api/[^'"`\s]*)['"`]""")

# Paths that genuinely cannot be resolved statically.
IGNORED = {
    "/api",
}


def _normalise(raw: str) -> str:
    """Collapse interpolations to a placeholder segment and drop any query string."""
    path = INTERPOLATION_RE.sub("1", raw)
    path = path.split("?", 1)[0]
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


def _backend_routes() -> set[str]:
    return {route.path for route in app.routes if hasattr(route, "path")}


def _matches(called: str, declared: set[str]) -> bool:
    """A call matches a declared route directly or via a path parameter."""
    if called in declared:
        return True
    called_parts = called.strip("/").split("/")
    for route in declared:
        route_parts = route.strip("/").split("/")
        if len(route_parts) != len(called_parts):
            continue
        if all(
            r.startswith("{") or r == c
            for r, c in zip(route_parts, called_parts)
        ):
            return True
    return False


def test_frontend_scan_finds_endpoints():
    """Guard the guard: if the scan returns nothing, the test below is vacuous."""
    assert len(_frontend_api_paths()) > 10


@pytest.mark.parametrize("called", sorted(_frontend_api_paths()))
def test_frontend_endpoint_exists_in_backend(called):
    declared = _backend_routes()
    assert _matches(called, declared), (
        f"The frontend calls {called} but the backend declares no such route. "
        f"Users hitting this feature get a 404."
    )


def test_no_duplicate_route_paths():
    """FastAPI serves the first match, so a duplicate path silently disables the later handler."""
    seen: dict[tuple[str, str], int] = {}
    for route in app.routes:
        for method in getattr(route, "methods", set()) or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            key = (method, route.path)
            seen[key] = seen.get(key, 0) + 1
    duplicates = {k: v for k, v in seen.items() if v > 1}
    assert not duplicates, f"Duplicate route registrations shadow later handlers: {duplicates}"
