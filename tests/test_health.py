"""Health endpoints must report what they actually find.

/health used to return a hard-coded {"database": "connected"} without ever
opening a connection. The deployed Postgres instance was deleted, every
database-backed endpoint returned 500, and this endpoint kept answering
"healthy" -- so the platform's health gate passed and the outage stayed
invisible. The observed error was:

    psycopg2.OperationalError: could not translate host name
    "dpg-...-a" to address: Name or service not known

Separately, Base.metadata.create_all(bind=engine) ran at import time in both
backend/main.py and backend/bot.py, so an unreachable database took the process
down before it could serve anything -- including the endpoint that would have
explained why.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _unreachable_database():
    """Make every connection attempt fail the way a deleted host does."""
    return patch(
        "backend.main.engine.connect",
        side_effect=OSError("could not translate host name to address"),
    )


def test_health_reports_a_reachable_database(client):
    body = client.get("/health").json()
    assert body["services"]["database"] == "connected"
    assert body["status"] == "healthy"


def test_health_does_not_claim_connected_when_the_database_is_gone(client):
    """The exact failure that hid a multi-day outage."""
    with _unreachable_database():
        response = client.get("/health")
        body = response.json()

    assert body["services"]["database"] != "connected", (
        "/health reported the database as connected without reaching it."
    )
    assert body["status"] == "degraded"


def test_health_stays_200_when_a_dependency_is_down(client):
    """Liveness must not flap.

    Restarting the process will not bring a deleted database back, so returning
    503 here would only add a restart loop to the outage.
    """
    with _unreachable_database():
        assert client.get("/health").status_code == 200


def test_readiness_returns_503_when_the_database_is_unreachable(client):
    """Readiness is what alerting and load-balancer membership should watch."""
    with _unreachable_database():
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


def test_readiness_returns_200_when_healthy(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["services"]["database"] == "connected"


def test_health_does_not_leak_connection_details(client):
    """This endpoint is public; a driver error carries host and credentials."""
    with patch(
        "backend.main.engine.connect",
        side_effect=OSError(
            'could not translate host name "dpg-secret-host-a" to address; '
            "user=admin password=hunter2"
        ),
    ):
        body = client.get("/health").json()

    rendered = str(body)
    assert "hunter2" not in rendered
    assert "dpg-secret-host-a" not in rendered


def test_importing_the_app_does_not_require_a_database():
    """The app must boot well enough to explain that its database is missing.

    create_all() at import time meant an unreachable database was a hard import
    failure, so the process could not start and nothing could report why.
    """
    import backend.bot
    import backend.main

    source = (
        __import__("pathlib").Path(backend.main.__file__).read_text(encoding="utf-8")
        + __import__("pathlib").Path(backend.bot.__file__).read_text(encoding="utf-8")
    )
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "create_all(bind=" not in stripped, (
            "Schema creation moved back into the import path. Alembic owns the "
            "schema; an import-time create_all takes the process down whenever "
            "the database is briefly unreachable."
        )
