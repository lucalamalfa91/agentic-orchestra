"""
Database configuration and session management for Orchestrator UI.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Determine project root (go up from backend/ to agentic-orchestra/)
project_root = Path(__file__).parent.parent.parent
db_dir = project_root / "database"
db_dir.mkdir(parents=True, exist_ok=True)

# Get database URL from environment or use default
default_db_url = f"sqlite:///{db_dir / 'orchestrator.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Use with FastAPI Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Also refreshes metadata to avoid SQLAlchemy cache issues.
    """
    try:
        from orchestrator_ui.backend import models  # Import models to register them
    except ModuleNotFoundError:
        import models  # Fallback for direct script execution

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # CRITICAL: Reflect existing tables to refresh SQLAlchemy metadata cache
    # This ensures SQLAlchemy sees columns added by migrations
    Base.metadata.reflect(bind=engine, extend_existing=True)

    print("Database initialized successfully!")
