"""Remove example project from database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from orchestrator_ui.backend.database import SessionLocal
    from orchestrator_ui.backend import models
except ModuleNotFoundError:
    import database
    import models
    SessionLocal = database.SessionLocal

db = SessionLocal()

# Find and delete example project
example = db.query(models.Project).filter(
    models.Project.id == 1
).first()

if example:
    print("Removing example project: {}".format(example.name))
    db.delete(example)
    db.commit()
    print("Removed!")
else:
    print("Example project not found")

db.close()
