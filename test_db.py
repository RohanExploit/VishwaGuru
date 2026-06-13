from sqlalchemy import text
from backend.database import engine

def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Database connection successful: {result.fetchone()}")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    test_db()
