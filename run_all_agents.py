# app-factory/run_all_agents.py
from AI_agents.ai_utils import write_readme
from AI_agents.design_agent import main as run_design
from AI_agents.backend_agent import main as run_backend
from AI_agents.frontend_agent import main as run_frontend
from AI_agents.devops_agent import main as run_devops
from AI_agents.publish_agent import main as run_publish

def main():
    print("RUN ALL AGENTS (output in generated_app/)\n")

    write_readme()
    print("\n--- README update completed ---\n")

    run_design()
    print("\n--- Design completed ---\n")

    run_backend()
    print("\n--- Backend completed ---\n")

    run_frontend()
    print("\n--- Frontend completed ---\n")

    run_devops()
    print("\n--- DevOps completed ---\n")

    run_publish()
    print("\n--- Publish completed ---\n")

    print("ALL DONE. App published to GitHub and deployment instructions provided.")

if __name__ == "__main__":
    main()
