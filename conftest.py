"""Pytest bootstrap.

Guarantees the repository root is importable so `backend.*` resolves from any
test, and asserts that backend/ never lands on sys.path. Putting backend/ on the
path lets `models` and `backend.models` both import as separate modules, which
registers every SQLAlchemy table twice and made `backend.main` fail at import.
Individual test files used to do this themselves with sys.path hacks.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def pytest_configure(config):
    """Drop backend/ from sys.path if any module put it there on import."""
    backend = str(BACKEND_DIR)
    while backend in sys.path:
        sys.path.remove(backend)
