# AI_agents/devops_agent.py
from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP4: DevOps (GitHub Actions) ===")
    design = read_utf8("design.yaml")

    prompt = f"""
    Design:

    {design}

    Write YAML for .github/workflows/deploy.yml that:
    - trigger: push to main
    - job build-backend: dotnet build + docker build/push to ACR crsharedacrcorchn001
    - job build-frontend: npm ci && npm run build
    - job deploy: use Azure CLI to deploy ACA (backend) and Static Web App (frontend).

    CRITICAL CONSTRAINTS:
    - DO NOT use markdown code blocks
    - DO NOT use language markers (no ```yaml, no ```)
    - Respond ONLY with valid YAML
    - Write ALL job names, step names, comments, messages in ENGLISH only
    - Use English for all workflow names, descriptions, and output messages
    """

    workflow_yaml = call_ai(
        prompt,
        system_content="You are an Azure/GitHub Actions DevOps engineer. Write EVERYTHING in English only."
    )
    app_tsx = strip_markdown_fences(workflow_yaml)
    write_utf8(".github/workflows/deploy.yml", workflow_yaml)

if __name__ == "__main__":
    main()
