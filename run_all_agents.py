# app-factory/run_all_agents.py
from AI_agents.ai_utils import write_readme
from AI_agents.architect_agent import main as run_architect
from AI_agents.uxui_agent import main as run_uxui
from AI_agents.backend_agent import main as run_backend
from AI_agents.frontend_agent import main as run_frontend
from AI_agents.devops_agent import main as run_devops
from AI_agents.publish_agent import main as run_publish

def main():
    print("=" * 80)
    print("AGENTIC ORCHESTRA - Full Stack App Generation")
    print("=" * 80)

    write_readme()
    print("\n=== STEP 0: README - COMPLETED ===")
    print("Output: README.md\n")

    run_architect()
    print("\n=== STEP 1: Architecture - COMPLETED ===")
    print("Output: design.yaml, docs/architecture.md, docs/db_design.puml\n")

    run_uxui()
    print("\n=== STEP 1.5: UX/UI Design System - COMPLETED ===")
    print("Output: uxui_design.json\n")

    run_backend()
    print("\n=== STEP 2: Backend - COMPLETED ===")
    print("Output: backend/Program.cs, backend/Models/, backend/Services/\n")

    run_frontend()
    print("\n=== STEP 3: Frontend + Design System - COMPLETED ===")
    print("Output: frontend/App.tsx, frontend/src/index.css, frontend/src/uxui_design.json\n")

    run_devops()
    print("\n=== STEP 4: DevOps - COMPLETED ===")
    print("Output: .github/workflows/\n")

    run_publish()
    print("\n=== STEP 5: Publish - COMPLETED ===")
    print("Output: Repository pushed to GitHub\n")

    print("=" * 80)
    print("🎉 ALL DONE! Your app is ready and published! 🎉")
    print("=" * 80)

if __name__ == "__main__":
    main()
