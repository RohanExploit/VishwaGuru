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

# Matches '/api/...' inside quotes or template literals in JS/JSX sources.
API_PATH_RE = re.compile(r"""['"`](/api/[a-zA-Z0-9/_\-]+)['"`]""")

# Paths built at runtime from an id, which the static scan cannot resolve.
IGNORED = {
    "/api/",
}


def _frontend_api_paths() -> set[str]:
    paths: set[str] = set()
    for path in FRONTEND_SRC.rglob("*.js*"):
        if "__tests__" in path.parts or "__mocks__" in path.parts:
            continue
        for match in API_PATH_RE.findall(path.read_text(encoding="utf-8", errors="ignore")):
            if match not in IGNORED:
                paths.add(match.rstrip("/"))
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
