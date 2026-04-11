import sys
sys.path.insert(0, 'orchestrator-ui/backend')
from database import engine
from sqlalchemy import text

tables = ['users', 'projects', 'configurations', 'deploy_provider_auths', 'knowledge_sources']

with engine.connect() as conn:
    for table_name in tables:
        print(f"\n{'='*70}")
        print(f"{table_name.upper()} TABLE COLUMNS:")
        print(f"{'='*70}")
        try:
            result = conn.execute(text(f'PRAGMA table_info({table_name})'))
            for row in result:
                print(f"  {row[1]:30s} {row[2]:20s} NOT NULL={row[3]}")
        except Exception as e:
            print(f"  ERROR: {e}")
print(f"\n{'='*70}\n")
