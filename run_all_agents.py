# app-factory/run_all_agents.py
from AI_agents.design_agent import main as run_design
from AI_agents.backend_agent import main as run_backend
from AI_agents.frontend_agent import main as run_frontend
from AI_agents.devops_agent import main as run_devops

def main():
    print("🚀 RUN ALL AGENTS (output in app-generated/)\n")

    run_design()
    print("\n--- design completato ---\n")

    run_backend()
    print("\n--- backend completato ---\n")

    run_frontend()
    print("\n--- frontend completato ---\n")

    run_devops()
    print("\n--- devops completato ---\n")

    print("✅ TUTTO FATTO. Controlla app-generated/ e poi:")
    print("cd app-generated/")
    print("git init && git add . && git commit -m \"AI factory\" && git push")

if __name__ == "__main__":
    main()
