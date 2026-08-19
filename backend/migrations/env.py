"""Alembic environment.

The database URL comes from the application's own configuration rather than
alembic.ini, so migrations always target the same database the service does and
there is no second place to keep in sync.

Batch mode is on because SQLite is the local fallback and cannot ALTER a column
in place; without it, any migration that changes or drops a column fails there
while passing against PostgreSQL.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Alembic runs this file directly, so the repository root has to be importable
# before `backend.*` will resolve.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.database import SQLALCHEMY_DATABASE_URL  # noqa: E402
from backend.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Escape '%' so ConfigParser interpolation does not choke on a URL containing
# percent-encoded credentials.
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it, for review or manual apply."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Detect column type changes, which alembic ignores by default.
            compare_type=True,
            # Required for SQLite: it cannot ALTER a column, so alembic
            # rebuilds the table instead.
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
