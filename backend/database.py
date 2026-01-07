"""
Database Configuration and Connection Management

Configures SQLAlchemy ORM for both SQLite (development/testing) and PostgreSQL
(production) databases. Provides database session management and declarative base.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Check for DATABASE_URL (Render/Postgres) or fall back to SQLite
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    # Fix for SQLAlchemy requiring postgresql:// scheme
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./data/issues.db"
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

# Create database engine with appropriate configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# Create session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for model definitions
Base = declarative_base()


def get_db():
    """Database session dependency. Yields session, ensures cleanup after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
