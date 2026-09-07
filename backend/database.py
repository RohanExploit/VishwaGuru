"""Database engine and session factory.

DATABASE_URL is honoured when it works. When it does not, the service falls
back to local SQLite rather than failing every request.

That fallback exists because of a real outage: the Postgres instance the
deployment pointed at was deleted, its hostname stopped resolving, and every
database-backed endpoint returned 500 while the service kept reporting itself
healthy. A civic reporting app that cannot accept a report is useless, and an
unreachable database is not a reason to refuse to run at all.

The fallback is deliberately loud, never silent:

  * the failure is logged at ERROR with the reason,
  * /health reports "sqlite-fallback" and the service reads "degraded",
  * SQLITE_FALLBACK_ENABLED=false turns it off for deployments that would
    rather fail hard than write somewhere unexpected.

It is a stopgap, not a fix. On a platform with an ephemeral filesystem the
SQLite file does not survive a restart, so reports collected while degraded can
be lost. Repointing DATABASE_URL at a live database is the actual repair.
"""

import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

SQLITE_URL = "sqlite:///./data/issues.db"
SQLITE_CONNECT_ARGS = {"check_same_thread": False}

# How long to wait for the configured database before giving up on it. Short on
# purpose: this runs during startup, and a suspended platform instance is
# already slow to boot.
CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))

_FALLBACK_ENABLED = os.environ.get("SQLITE_FALLBACK_ENABLED", "true").lower() not in {
    "0",
    "false",
    "no",
}


def _normalise(url: str) -> str:
    """SQLAlchemy dropped the postgres:// alias; several hosts still emit it."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _connect_args_for(url: str) -> dict:
    if url.startswith("sqlite"):
        return dict(SQLITE_CONNECT_ARGS)
    if url.startswith("postgresql"):
        # Without this a dead host hangs the boot until the OS gives up.
        return {"connect_timeout": CONNECT_TIMEOUT_SECONDS}
    return {}


def _is_reachable(candidate_engine) -> tuple[bool, str]:
    try:
        with candidate_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _build_engine() -> tuple[object, str, bool]:
    """Return (engine, url, using_fallback)."""
    configured = os.environ.get("DATABASE_URL", "").strip()

    if not configured:
        logger.info("DATABASE_URL is not set; using local SQLite at %s", SQLITE_URL)
        return (
            create_engine(SQLITE_URL, connect_args=_connect_args_for(SQLITE_URL)),
            SQLITE_URL,
            False,
        )

    url = _normalise(configured)
    candidate = create_engine(url, connect_args=_connect_args_for(url), pool_pre_ping=True)

    reachable, reason = _is_reachable(candidate)
    if reachable:
        return candidate, url, False

    if not _FALLBACK_ENABLED:
        logger.error(
            "Configured database is unreachable and SQLITE_FALLBACK_ENABLED is off. "
            "Refusing to start against a database that does not answer. Reason: %s",
            reason,
        )
        raise RuntimeError(f"Configured database is unreachable: {reason}")

    logger.error(
        "Configured database is unreachable, falling back to local SQLite. "
        "Data written while degraded may not survive a restart on an ephemeral "
        "filesystem. Repoint DATABASE_URL at a live database. Reason: %s",
        reason,
    )
    candidate.dispose()
    return (
        create_engine(SQLITE_URL, connect_args=_connect_args_for(SQLITE_URL)),
        SQLITE_URL,
        True,
    )


# `data/` must exist before SQLite will create a file inside it.
os.makedirs("data", exist_ok=True)

engine, SQLALCHEMY_DATABASE_URL, USING_SQLITE_FALLBACK = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
