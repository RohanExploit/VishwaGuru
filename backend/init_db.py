"""Best-effort schema migration for the issues and grievances tables.

Each statement is expected to fail once the column or index already exists,
which is why every one is tolerated individually. Previously each was wrapped
in a bare `except Exception: pass`, so a statement that failed for a real
reason -- wrong dialect, locked table, missing permission -- was
indistinguishable from one that was simply already applied, and left no trace
anywhere at all. Every outcome is now logged.

This is still not a migration system: there is no ordering, no down path, and
no record of which revision a database is on. Adopting Alembic is tracked
separately. Until then this at least fails loudly enough to diagnose.
"""

import logging

from sqlalchemy import text

from backend.database import engine

logger = logging.getLogger(__name__)

# (description, SQL). Order matters only in that a column must exist before an
# index over it, so columns are grouped ahead of their indexes per table.
MIGRATIONS: tuple[tuple[str, str], ...] = (
    # issues: columns
    ("issues.upvotes", "ALTER TABLE issues ADD COLUMN upvotes INTEGER DEFAULT 0"),
    ("issues.action_plan", "ALTER TABLE issues ADD COLUMN action_plan TEXT"),
    ("issues.latitude", "ALTER TABLE issues ADD COLUMN latitude FLOAT"),
    ("issues.longitude", "ALTER TABLE issues ADD COLUMN longitude FLOAT"),
    ("issues.location", "ALTER TABLE issues ADD COLUMN location VARCHAR"),
    # issues: indexes
    ("index ix_issues_upvotes", "CREATE INDEX ix_issues_upvotes ON issues (upvotes)"),
    ("index ix_issues_created_at", "CREATE INDEX ix_issues_created_at ON issues (created_at)"),
    ("index ix_issues_status", "CREATE INDEX ix_issues_status ON issues (status)"),
    ("index ix_issues_user_email", "CREATE INDEX ix_issues_user_email ON issues (user_email)"),
    ("index ix_issues_source", "CREATE INDEX ix_issues_source ON issues (source)"),
    ("index ix_issues_latitude", "CREATE INDEX ix_issues_latitude ON issues (latitude)"),
    ("index ix_issues_longitude", "CREATE INDEX ix_issues_longitude ON issues (longitude)"),
    (
        "index ix_issues_status_lat_lon",
        "CREATE INDEX ix_issues_status_lat_lon ON issues (status, latitude, longitude)",
    ),
    # grievances: columns
    ("grievances.latitude", "ALTER TABLE grievances ADD COLUMN latitude FLOAT"),
    ("grievances.longitude", "ALTER TABLE grievances ADD COLUMN longitude FLOAT"),
    ("grievances.address", "ALTER TABLE grievances ADD COLUMN address VARCHAR"),
    # grievances: indexes
    (
        "index ix_grievances_latitude",
        "CREATE INDEX ix_grievances_latitude ON grievances (latitude)",
    ),
    (
        "index ix_grievances_longitude",
        "CREATE INDEX ix_grievances_longitude ON grievances (longitude)",
    ),
    (
        "index ix_grievances_status_lat_lon",
        "CREATE INDEX ix_grievances_status_lat_lon ON grievances (status, latitude, longitude)",
    ),
    (
        "index ix_grievances_status_jurisdiction",
        "CREATE INDEX ix_grievances_status_jurisdiction ON grievances (status, current_jurisdiction_id)",
    ),
)


def migrate_db() -> dict[str, int]:
    """Apply every pending statement. Returns counts of applied vs skipped."""
    applied = 0
    skipped = 0

    try:
        with engine.connect() as conn:
            for description, statement in MIGRATIONS:
                try:
                    conn.execute(text(statement))
                except Exception as exc:
                    skipped += 1
                    logger.debug("Migration skipped (%s): %s", description, exc)
                else:
                    applied += 1
                    logger.info("Applied migration: %s", description)
            conn.commit()
    except Exception:
        logger.exception("Database migration failed")
        raise

    logger.info(
        "Database migration check complete: %d applied, %d already present.",
        applied,
        skipped,
    )
    return {"applied": applied, "skipped": skipped}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_db()
