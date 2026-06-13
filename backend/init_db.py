from sqlalchemy import text
from database import engine

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
                print("Migrated database: Added upvotes column.")
            except Exception:
                # Column likely already exists
                pass

            # Check if index exists or create it
            try:
                conn.execute(text("CREATE INDEX ix_issues_upvotes ON issues (upvotes)"))
                print("Migrated database: Added index on upvotes column.")
            except Exception:
                # Index likely already exists
                pass

            # Add index on created_at for faster sorting
            try:
                conn.execute(text("CREATE INDEX ix_issues_created_at ON issues (created_at)"))
                print("Migrated database: Added index on created_at column.")
            except Exception:
                # Index likely already exists
                pass

            # Add index on status for faster filtering
            try:
                conn.execute(text("CREATE INDEX ix_issues_status ON issues (status)"))
                print("Migrated database: Added index on status column.")
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

            conn.commit()
            print("Database migration check completed.")
    except Exception as e:
        print(f"Database migration error: {e}")
