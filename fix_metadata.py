"""
Fix SQLAlchemy metadata cache issue by disposing and recreating the engine.
This forces SQLAlchemy to reload the database schema from the actual DB.
"""
import sys
sys.path.insert(0, 'orchestrator-ui/backend')

print("Disposing old SQLAlchemy engine...")
from database import engine
engine.dispose()
print("✓ Engine disposed")

print("\nReloading database module...")
import importlib
import database as db_module
importlib.reload(db_module)
print("✓ Database module reloaded")

print("\nNew engine created. Testing access to columns...")
from sqlalchemy import text
with db_module.engine.connect() as conn:
    # Test configurations.ai_provider
    result = conn.execute(text("SELECT ai_provider FROM configurations LIMIT 1"))
    print("✓ configurations.ai_provider accessible")

    # Test projects.user_id
    result = conn.execute(text("SELECT user_id FROM projects LIMIT 1"))
    print("✓ projects.user_id accessible")

print("\n SUCCESS! Metadata cache cleared. Restart backend to apply.")
