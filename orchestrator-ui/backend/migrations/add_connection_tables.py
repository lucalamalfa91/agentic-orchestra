"""
Migration: Add User, Configuration, and DeployProviderAuth tables.

This migration creates three new tables:
- users: Store GitHub OAuth authenticated users
- configurations: Store AI provider configurations per user
- deploy_provider_auth: Store deployment provider authentication tokens

Run with: python -m orchestrator_ui.backend.migrations.add_connection_tables
Or simply reinitialize the database: python orchestrator-ui/backend/init_db.py
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent.parent))
sys.path.insert(0, str(current_dir.parent))

from sqlalchemy import create_engine, inspect
from database import DATABASE_URL, Base
from models import User, Configuration, DeployProviderAuth


def run_migration():
    """
    Create new tables if they don't exist.
    """
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    tables_to_create = []

    if "users" not in existing_tables:
        tables_to_create.append(User.__table__)
        print("  + Will create table: users")
    else:
        print("  - Table already exists: users")

    if "configurations" not in existing_tables:
        tables_to_create.append(Configuration.__table__)
        print("  + Will create table: configurations")
    else:
        print("  - Table already exists: configurations")

    if "deploy_provider_auth" not in existing_tables:
        tables_to_create.append(DeployProviderAuth.__table__)
        print("  + Will create table: deploy_provider_auth")
    else:
        print("  - Table already exists: deploy_provider_auth")

    if tables_to_create:
        print("\nCreating tables...")
        Base.metadata.create_all(bind=engine, tables=tables_to_create)
        print("Migration completed successfully!")
    else:
        print("\nNo tables to create. All tables already exist.")


if __name__ == "__main__":
    print("Running migration: add_connection_tables")
    print("=" * 50)
    run_migration()
