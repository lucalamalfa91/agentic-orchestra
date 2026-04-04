"""List all projects in database."""
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
projects = db.query(models.Project).all()

print("=== Projects in Database ===\n")
for p in projects:
    print("ID: {}".format(p.id))
    print("Name: {}".format(p.name))
    print("Description: {}".format(p.description))
    print("GitHub: {}".format(p.github_repo_url))
    print("Status: {}".format(p.status))
    print("Created: {}".format(p.created_at))

    # Get requirements
    req = db.query(models.ProjectRequirement).filter(
        models.ProjectRequirement.project_id == p.id
    ).first()
    if req:
        print("Frontend: {}".format(req.frontend_framework))
        print("Backend: {}".format(req.backend_framework))
        print("Database: {}".format(req.database_type))
        print("Deploy: {}".format(req.deploy_platform))

    print("-" * 50)

print("\nTotal projects: {}".format(len(projects)))
db.close()
