import sys
sys.path.insert(0, 'orchestrator-ui/backend')
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('PRAGMA table_info(configurations)'))
    print("\nCONFIGURATIONS TABLE COLUMNS:")
    print("=" * 60)
    for row in result:
        print(f"{row[1]:30s} {row[2]:20s} NOT NULL={row[3]}")
    print("=" * 60)
