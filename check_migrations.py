import sys
sys.path.insert(0, 'orchestrator-ui/backend')
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if alembic_version table exists
    try:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        print("Applied Alembic migrations:")
        for v in versions:
            print(f"  - {v[0]}")
    except Exception as e:
        print(f"Error: {e}")
        print("(alembic_version table may not exist)")
