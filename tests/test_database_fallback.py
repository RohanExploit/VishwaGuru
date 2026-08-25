"""An unreachable database must degrade the service, not disable it.

The deployment's Postgres instance was deleted. Its hostname stopped resolving,
every database-backed endpoint returned 500, and the app could not even start
once schema creation moved out of the import path:

    psycopg2.OperationalError: could not translate host name
    "dpg-d5h3qaali9vc73a7iqog-a" to address: Name or service not known

A civic reporting app that cannot accept a report is useless. backend/database
now probes the configured database at startup and falls back to local SQLite
when it cannot be reached -- loudly, and visibly in /health, because a service
that works is not the same as a service that is configured correctly.
"""

import importlib
import logging

import pytest

DEAD_POSTGRES = "postgresql://user:pass@dpg-does-not-resolve-a:5432/db"


def _reload_database(monkeypatch, **env):
    """Re-import backend.database with a given environment.

    The engine is chosen at import time, so the module has to be reloaded for
    each scenario rather than patched afterwards.
    """
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    import backend.database as database

    return importlib.reload(database)


@pytest.fixture(autouse=True)
def restore_modules():
    """Rebind both modules to the ambient environment afterwards.

    backend.main captures USING_SQLITE_FALLBACK at import, so reloading only
    backend.database would leave every later test seeing a service that thinks
    it is running on the fallback.
    """
    yield

    import backend.database as database

    importlib.reload(database)

    import backend.main as main_module

    importlib.reload(main_module)


def test_unset_url_uses_sqlite_without_claiming_a_fallback(monkeypatch):
    database = _reload_database(monkeypatch, DATABASE_URL=None)

    assert database.SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    # Not a fallback: no database was configured, so nothing failed.
    assert database.USING_SQLITE_FALLBACK is False


def test_unreachable_database_falls_back_instead_of_raising(monkeypatch):
    database = _reload_database(monkeypatch, DATABASE_URL=DEAD_POSTGRES)

    assert database.USING_SQLITE_FALLBACK is True
    assert database.SQLALCHEMY_DATABASE_URL.startswith("sqlite")


def test_fallback_is_logged_at_error(monkeypatch, caplog):
    """A silent fallback would hide the outage all over again."""
    with caplog.at_level(logging.ERROR, logger="backend.database"):
        _reload_database(monkeypatch, DATABASE_URL=DEAD_POSTGRES)

    messages = " ".join(record.message for record in caplog.records)
    assert "falling back" in messages.lower()
    assert "DATABASE_URL" in messages


def test_fallback_can_be_refused(monkeypatch):
    """Some deployments would rather fail hard than write somewhere unexpected."""
    with pytest.raises(RuntimeError, match="unreachable"):
        _reload_database(
            monkeypatch,
            DATABASE_URL=DEAD_POSTGRES,
            SQLITE_FALLBACK_ENABLED="false",
        )


def test_postgres_scheme_alias_is_normalised(monkeypatch):
    """SQLAlchemy dropped postgres://; several hosts still hand it out."""
    database = _reload_database(
        monkeypatch, DATABASE_URL="postgres://user:pass@dpg-does-not-resolve-a:5432/db"
    )
    # It still cannot connect, but it must have failed as postgresql, not by
    # rejecting the URL scheme outright.
    assert database.USING_SQLITE_FALLBACK is True


def test_health_distinguishes_fallback_from_healthy(monkeypatch):
    """A working service is not the same as a correctly configured one."""
    _reload_database(monkeypatch, DATABASE_URL=DEAD_POSTGRES)

    import backend.main as main_module

    importlib.reload(main_module)

    from fastapi.testclient import TestClient

    with TestClient(main_module.app) as client:
        body = client.get("/health").json()
        ready = client.get("/health/ready")

    assert "fallback" in body["services"]["database"]
    assert body["status"] == "degraded"
    # Readiness stays failing: the deployment is still misconfigured.
    assert ready.status_code == 503
