import sys
import os
from pathlib import Path
from sqlalchemy import text, inspect
import logging

# Add project root to path
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
repo_root = backend_dir.parent
sys.path.insert(0, str(repo_root))

from backend.database import engine, Base
from backend.models import *

logger = logging.getLogger(__name__)

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

def migrate_db():
    """
    Perform database migrations using SQLAlchemy inspection.
    This prevents transaction aborts in Postgres when columns already exist.
    """
    try:
        inspector = inspect(engine)

        # Helper to check column existence
        def column_exists(table, column):
            if not inspector.has_table(table):
                return False
            columns = [c["name"] for c in inspector.get_columns(table)]
            return column in columns

        # Helper to check index existence (by name)
        def index_exists(table, index_name):
            if not inspector.has_table(table):
                return False
            indexes = [i["name"] for i in inspector.get_indexes(table)]
            return index_name in indexes

        with engine.begin() as conn:
            # Issues Table Migrations
            if inspector.has_table("issues"):
                if not column_exists("issues", "upvotes"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN upvotes INTEGER DEFAULT 0"))
                    logger.info("Added upvotes column to issues")

                if not column_exists("issues", "latitude"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN latitude FLOAT"))
                    logger.info("Added latitude column to issues")

                if not column_exists("issues", "longitude"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN longitude FLOAT"))
                    logger.info("Added longitude column to issues")

                if not column_exists("issues", "location"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN location VARCHAR"))
                    logger.info("Added location column to issues")

                if not column_exists("issues", "action_plan"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN action_plan TEXT"))
                    logger.info("Added action_plan column to issues")

                if not column_exists("issues", "integrity_hash"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN integrity_hash VARCHAR"))
                    logger.info("Added integrity_hash column to issues")

                if not column_exists("issues", "previous_integrity_hash"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN previous_integrity_hash VARCHAR"))
                    logger.info("Added previous_integrity_hash column to issues")

                # Indexes (using IF NOT EXISTS syntax where supported or check first)
                if not index_exists("issues", "ix_issues_upvotes"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_upvotes ON issues (upvotes)"))

                if not index_exists("issues", "ix_issues_created_at"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_created_at ON issues (created_at)"))

                if not index_exists("issues", "ix_issues_status"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_status ON issues (status)"))

                if not index_exists("issues", "ix_issues_latitude"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_latitude ON issues (latitude)"))

                if not index_exists("issues", "ix_issues_longitude"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_longitude ON issues (longitude)"))

                if not index_exists("issues", "ix_issues_status_lat_lon"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_status_lat_lon ON issues (status, latitude, longitude)"))

                if not index_exists("issues", "ix_issues_user_email"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_issues_user_email ON issues (user_email)"))

                # Voice and Language Support Columns (Issue #291)
                if not column_exists("issues", "submission_type"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN submission_type VARCHAR DEFAULT 'text'"))
                    logger.info("Added submission_type column to issues")

                if not column_exists("issues", "original_language"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN original_language VARCHAR"))
                    logger.info("Added original_language column to issues")

                if not column_exists("issues", "original_text"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN original_text TEXT"))
                    logger.info("Added original_text column to issues")

                if not column_exists("issues", "transcription_confidence"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN transcription_confidence FLOAT"))
                    logger.info("Added transcription_confidence column to issues")

                if not column_exists("issues", "manual_correction_applied"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN manual_correction_applied BOOLEAN DEFAULT FALSE"))
                    logger.info("Added manual_correction_applied column to issues")

                if not column_exists("issues", "audio_file_path"):
                    conn.execute(text("ALTER TABLE issues ADD COLUMN audio_file_path VARCHAR"))
                    logger.info("Added audio_file_path column to issues")

            # Grievances Table Migrations
            if inspector.has_table("grievances"):
                if not column_exists("grievances", "latitude"):
                    conn.execute(text("ALTER TABLE grievances ADD COLUMN latitude FLOAT"))
                    logger.info("Added latitude column to grievances")

                if not column_exists("grievances", "longitude"):
                    conn.execute(text("ALTER TABLE grievances ADD COLUMN longitude FLOAT"))
                    logger.info("Added longitude column to grievances")

                if not column_exists("grievances", "address"):
                    conn.execute(text("ALTER TABLE grievances ADD COLUMN address VARCHAR"))
                    logger.info("Added address column to grievances")

                if not column_exists("grievances", "issue_id"):
                    conn.execute(text("ALTER TABLE grievances ADD COLUMN issue_id INTEGER"))
                    logger.info("Added issue_id column to grievances")

                # Indexes
                if not index_exists("grievances", "ix_grievances_latitude"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_latitude ON grievances (latitude)"))

                if not index_exists("grievances", "ix_grievances_longitude"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_longitude ON grievances (longitude)"))

                if not index_exists("grievances", "ix_grievances_status_lat_lon"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_status_lat_lon ON grievances (status, latitude, longitude)"))

                if not index_exists("grievances", "ix_grievances_status_jurisdiction"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_status_jurisdiction ON grievances (status, current_jurisdiction_id)"))

                if not index_exists("grievances", "ix_grievances_issue_id"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_issue_id ON grievances (issue_id)"))

                if not index_exists("grievances", "ix_grievances_assigned_authority"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_assigned_authority ON grievances (assigned_authority)"))

                if not index_exists("grievances", "ix_grievances_category_status"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_grievances_category_status ON grievances (category, status)"))

            # Field Officer Visits Table (Issue #288)
            # This table is newly created for field officer check-in system
            if not inspector.has_table("field_officer_visits"):
                logger.info("Creating field_officer_visits table...")
                # Use conn.execute to stay within the transaction
                Base.metadata.tables['field_officer_visits'].create(bind=conn)
                logger.info("Created field_officer_visits table")
            
            # Indexes for field_officer_visits (run regardless of table creation)
            if inspector.has_table("field_officer_visits"):
                if not index_exists("field_officer_visits", "ix_field_officer_visits_issue_id"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_field_officer_visits_issue_id ON field_officer_visits (issue_id)"))
                
                if not index_exists("field_officer_visits", "ix_field_officer_visits_officer_email"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_field_officer_visits_officer_email ON field_officer_visits (officer_email)"))
                
                if not index_exists("field_officer_visits", "ix_field_officer_visits_status"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_field_officer_visits_status ON field_officer_visits (status)"))
                
                if not index_exists("field_officer_visits", "ix_field_officer_visits_check_in_time"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_field_officer_visits_check_in_time ON field_officer_visits (check_in_time)"))

            logger.info("Database migration check completed successfully.")

    except Exception as e:
        logger.error(f"Database migration error: {e}", exc_info=True)
        # Re-raise to alert deployment failure if migration is critical
        # raise e

if __name__ == "__main__":
    init_db()
    migrate_db()
