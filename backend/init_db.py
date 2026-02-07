from sqlalchemy import text
from backend.database import engine
import logging

logger = logging.getLogger(__name__)

def migrate_db():
    """
    Perform database migrations.
    This is a simple MVP migration strategy.
    """
    try:
        with engine.connect() as conn:
            # Check for upvotes column and add if missing
            try:
                # SQLite doesn't support IF NOT EXISTS in ALTER TABLE
                # So we just try to add it and ignore error if it exists
                conn.execute(text("ALTER TABLE issues ADD COLUMN upvotes INTEGER DEFAULT 0"))
                logger.info("Migrated database: Added upvotes column.")
            except Exception:
                # Column likely already exists
                pass

            # Check if index exists or create it
            try:
                conn.execute(text("CREATE INDEX ix_issues_upvotes ON issues (upvotes)"))
                logger.info("Migrated database: Added index on upvotes column.")
            except Exception:
                # Index likely already exists
                pass

            # Add index on created_at for faster sorting
            try:
                conn.execute(text("CREATE INDEX ix_issues_created_at ON issues (created_at)"))
                logger.info("Migrated database: Added index on created_at column.")
            except Exception:
                # Index likely already exists
                pass

            # Add index on status for faster filtering
            try:
                conn.execute(text("CREATE INDEX ix_issues_status ON issues (status)"))
                logger.info("Migrated database: Added index on status column.")
            except Exception:
                # Index likely already exists
                pass

            # Add latitude column
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN latitude FLOAT"))
                print("Migrated database: Added latitude column.")
            except Exception:
                pass

            # Add longitude column
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN longitude FLOAT"))
                print("Migrated database: Added longitude column.")
            except Exception:
                pass

            # Add index on latitude for faster spatial queries
            try:
                conn.execute(text("CREATE INDEX ix_issues_latitude ON issues (latitude)"))
                logger.info("Migrated database: Added index on latitude column.")
            except Exception:
                # Index likely already exists
                pass

            # Add index on longitude for faster spatial queries
            try:
                conn.execute(text("CREATE INDEX ix_issues_longitude ON issues (longitude)"))
                logger.info("Migrated database: Added index on longitude column.")
            except Exception:
                # Index likely already exists
                pass

            # Add composite index for optimized spatial+status queries
            try:
                conn.execute(text("CREATE INDEX ix_issues_status_lat_lon ON issues (status, latitude, longitude)"))
                logger.info("Migrated database: Added composite index on status, latitude, longitude.")
            except Exception:
                # Index likely already exists
                pass

            # Add location column
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN location VARCHAR"))
                print("Migrated database: Added location column.")
            except Exception:
                pass

            # Add action_plan column
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN action_plan TEXT"))
                print("Migrated database: Added action_plan column.")
            except Exception:
                pass

            # Add integrity_hash column for blockchain feature
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN integrity_hash VARCHAR"))
                print("Migrated database: Added integrity_hash column.")
            except Exception:
                pass

            # Add index on user_email
            try:
                conn.execute(text("CREATE INDEX ix_issues_user_email ON issues (user_email)"))
                logger.info("Migrated database: Added index on user_email column.")
            except Exception:
                # Index likely already exists
                pass

            # --- Grievance Migrations ---
            # Add latitude column to grievances
            try:
                conn.execute(text("ALTER TABLE grievances ADD COLUMN latitude FLOAT"))
                logger.info("Migrated database: Added latitude column to grievances.")
            except Exception:
                pass

            # Add longitude column to grievances
            try:
                conn.execute(text("ALTER TABLE grievances ADD COLUMN longitude FLOAT"))
                logger.info("Migrated database: Added longitude column to grievances.")
            except Exception:
                pass

            # Add address column to grievances
            try:
                conn.execute(text("ALTER TABLE grievances ADD COLUMN address VARCHAR"))
                logger.info("Migrated database: Added address column to grievances.")
            except Exception:
                pass

            # Add index on latitude (grievances)
            try:
                conn.execute(text("CREATE INDEX ix_grievances_latitude ON grievances (latitude)"))
            except Exception:
                pass

            # Add index on longitude (grievances)
            try:
                conn.execute(text("CREATE INDEX ix_grievances_longitude ON grievances (longitude)"))
            except Exception:
                pass

            # Add composite index for spatial+status (grievances)
            try:
                conn.execute(text("CREATE INDEX ix_grievances_status_lat_lon ON grievances (status, latitude, longitude)"))
                logger.info("Migrated database: Added composite index on status, latitude, longitude for grievances.")
            except Exception:
                pass

            # Add composite index for status+jurisdiction (grievances)
            try:
                conn.execute(text("CREATE INDEX ix_grievances_status_jurisdiction ON grievances (status, current_jurisdiction_id)"))
                logger.info("Migrated database: Added composite index on status, jurisdiction for grievances.")
            except Exception:
                pass

            # Add issue_id column to grievances
            try:
                conn.execute(text("ALTER TABLE grievances ADD COLUMN issue_id INTEGER"))
                logger.info("Migrated database: Added issue_id column to grievances.")
            except Exception:
                pass

            # Add index on issue_id (grievances)
            try:
                conn.execute(text("CREATE INDEX ix_grievances_issue_id ON grievances (issue_id)"))
                logger.info("Migrated database: Added index on issue_id for grievances.")
            except Exception:
                pass

            # Add index on assigned_authority (grievances)
            try:
                conn.execute(text("CREATE INDEX ix_grievances_assigned_authority ON grievances (assigned_authority)"))
                logger.info("Migrated database: Added index on assigned_authority for grievances.")
            except Exception:
                pass

            # Add composite index for category+status (grievances) - Optimized for filtering
            try:
                conn.execute(text("CREATE INDEX ix_grievances_category_status ON grievances (category, status)"))
                logger.info("Migrated database: Added composite index on category, status for grievances.")
            except Exception:
                pass

            conn.commit()
            logger.info("Database migration check completed.")
    except Exception as e:
        logger.error(f"Database migration error: {e}")
