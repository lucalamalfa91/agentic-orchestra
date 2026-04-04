"""
Seed database with example project.
"""
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from orchestrator_ui.backend.database import SessionLocal
    from orchestrator_ui.backend import models
except ModuleNotFoundError:
    import database
    import models
    SessionLocal = database.SessionLocal

def seed_example_project():
    """Add Como Weather example project to database."""
    db = SessionLocal()

    try:
        # Check if example already exists
        existing = db.query(models.Project).filter(
            models.Project.name == "como-weather"
        ).first()

        if existing:
            print("⚠️  Como Weather example already exists in database")
            return

        # Create example project
        project = models.Project(
            name="como-weather",
            description="Weather app showing 7-day forecast for Como, Italy",
            github_repo_url="https://github.com/example/como-weather",
            status="completed",
            created_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Add requirements
        features = ["Display current temperature", "Show 7-day forecast", "Show precipitation and wind speed"]
        requirements_text = """Weather app showing 7-day forecast for Como, Italy

Features:
- Display current temperature
- Show 7-day forecast
- Show precipitation and wind speed

Technical:
- Frontend: react
- Backend: none
- Database: none
- Deploy to: github-pages"""

        requirement = models.ProjectRequirement(
            project_id=project.id,
            mvp_description="Weather app showing 7-day forecast for Como, Italy",
            features=json.dumps(features),
            user_stories=None,
            frontend_framework="react",
            backend_framework="none",
            database_type="none",
            deploy_platform="github-pages",
            requirements_text=requirements_text
        )
        db.add(requirement)

        # Add logs
        steps = [
            ("readme", "completed", "README update completed"),
            ("design", "completed", "Design phase completed"),
            ("backend", "completed", "Backend generation completed"),
            ("frontend", "completed", "Frontend generation completed"),
            ("devops", "completed", "DevOps pipeline completed"),
            ("publish", "completed", "Published to GitHub successfully")
        ]

        for step_name, status, message in steps:
            log = models.GenerationLog(
                project_id=project.id,
                step_name=step_name,
                status=status,
                message=message,
                created_at=datetime.utcnow()
            )
            db.add(log)

        db.commit()

        print(f"✅ Added Como Weather example project (ID: {project.id})")
        print(f"   - Features: {len(features)}")
        print(f"   - Logs: {len(steps)}")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding database with example project...")
    seed_example_project()
    print("Done!")
