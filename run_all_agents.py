# app-factory/run_all_agents.py
from AI_agents.ai_utils import write_readme 
from AI_agents.design_agent import main as run_design
from AI_agents.backend_agent import main as run_backend
from AI_agents.frontend_agent import main as run_frontend
from AI_agents.devops_agent import main as run_devops

def main():
    print("🚀 RUN ALL AGENTS (output in generated_app/)\n")

    write_readme()
    print("\n--- update readmefile ---\n")

    run_design()
    print("\n--- design completato ---\n")

    run_backend()
    print("\n--- backend completato ---\n")

    run_frontend()
    print("\n--- frontend completato ---\n")

    run_devops()
    print("\n--- devops completato ---\n")

    print("✅ TUTTO FATTO. Controlla generated_app/ E Pusha il tuo codice:")

if __name__ == "__main__":
    main()
