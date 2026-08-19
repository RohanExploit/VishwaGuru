"""Migrations must build the schema the models describe, and must reverse.

The schema was previously maintained by raw ALTER and CREATE INDEX statements
run on every startup, each wrapped in a bare `except: pass`. There was no
ordering, no down path, and no record of which revision a database was on, so a
statement that failed for a real reason was indistinguishable from one that was
simply already applied.

These tests fail if a model changes without a matching migration -- the failure
mode that would otherwise only appear as a 500 in production.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from backend.models import Base

REPO_ROOT = Path(__file__).resolve().parents[1]


def _alembic(*args: str, db_url: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=REPO_ROOT,
        env={
            **__import__("os").environ,
            "DATABASE_URL": db_url,
            "PYTHONPATH": str(REPO_ROOT),
        },
        capture_output=True,
        text=True,
    )


@pytest.fixture
def db_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'migrations.db').as_posix()}"


def test_upgrade_creates_every_table_the_models_declare(db_url):
    result = _alembic("upgrade", "head", db_url=db_url)
    assert result.returncode == 0, f"alembic upgrade failed:\n{result.stderr}"

    inspector = inspect(create_engine(db_url))
    created = set(inspector.get_table_names())
    expected = set(Base.metadata.tables)

    missing = expected - created
    assert not missing, f"Migrations did not create: {sorted(missing)}"


def test_upgrade_creates_every_column_the_models_declare(db_url):
    assert _alembic("upgrade", "head", db_url=db_url).returncode == 0

    inspector = inspect(create_engine(db_url))
    for table_name, table in Base.metadata.tables.items():
        actual = {c["name"] for c in inspector.get_columns(table_name)}
        expected = {c.name for c in table.columns}
        missing = expected - actual
        assert not missing, f"{table_name} is missing {sorted(missing)} after migrating."


def test_no_pending_model_changes(db_url):
    """`alembic check` fails when a model has drifted from the migrations.

    This is the guard: edit a model, forget the migration, and this test fails
    rather than production.
    """
    assert _alembic("upgrade", "head", db_url=db_url).returncode == 0

    result = _alembic("check", db_url=db_url)
    assert result.returncode == 0, (
        "Models have drifted from the migrations. Run:\n"
        "  alembic revision --autogenerate -m '<describe the change>'\n\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_downgrade_reverses_the_baseline(db_url):
    """A migration without a working down path cannot be rolled back in an incident."""
    assert _alembic("upgrade", "head", db_url=db_url).returncode == 0

    result = _alembic("downgrade", "base", db_url=db_url)
    assert result.returncode == 0, f"alembic downgrade failed:\n{result.stderr}"

    inspector = inspect(create_engine(db_url))
    remaining = set(inspector.get_table_names()) - {"alembic_version"}
    assert not remaining, f"Downgrade left tables behind: {sorted(remaining)}"
