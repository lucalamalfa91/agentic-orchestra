"""
Database initialization script.
Run this to create all database tables.
"""
import sys
from pathlib import Path

# Add current directory and parent directories to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))
sys.path.insert(0, str(current_dir))

# Import database and models directly
import database
import models

if __name__ == "__main__":
    print("Initializing database...")
    database.init_db()
    print("Database initialization complete!")
