# AI_agents/devops_agent.py
from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP4: DevOps (GitHub Actions) ===")
    design = read_utf8("design.yaml")

    prompt = f"""
    Design:

    {design}

    Scrivi YAML per .github/workflows/deploy.yml che:
    - trigger: push su main
    - job build-backend: dotnet build + docker build/push su ACR crsharedacrcorchn001
    - job build-frontend: npm ci && npm run build
    - job deploy: usa Azure CLI per deploy ACA (backend) e Static Web App (frontend).

    Vincoli:
    - NON usare blocchi di codice markdown.
    - NON usare marcatori di linguaggio (niente ```yaml, niente ```).
    - Rispondi SOLO con YAML valido.
    """

    workflow_yaml = call_ai(
        prompt,
        system_content="Sei un DevOps engineer Azure/GitHub Actions."
    )
    app_tsx = strip_markdown_fences(workflow_yaml)
    write_utf8(".github/workflows/deploy.yml", workflow_yaml)

if __name__ == "__main__":
    main()
