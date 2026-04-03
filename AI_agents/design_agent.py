# app-factory/AI_agents/design_agent.py
from .ai_utils import call_ai, write_utf8, BASE_DIR
from pathlib import Path

def main():
    print("=== STEP1: design + architecture + DB ===")

    # Read requirements dynamically from pipeline_data/requirements.txt
    requirements_file = BASE_DIR / "pipeline_data" / "requirements.txt"

    if requirements_file.exists():
        with open(requirements_file, "r", encoding="utf-8") as f:
            reqs = f.read()
        print(f"INFO Requirements loaded from {requirements_file}")
    else:
        # Fallback to default requirements
        reqs = """
        Simple Todo App:
        - FE: React + Tailwind (add/edit/delete/toggle todos)
        - BE: .NET 8 Minimal API + EF Core SQLite (/todos CRUD)
        - Deploy: Azure Container Apps (BE) + Static Web App (FE)
        - ACR: crsharedacrcorchn001
        - Test: xUnit/Jest
        """
        print("WARNING No requirements file found, using default requirements")

    # 1) DESIGN YAML
    prompt_design = f"""
    Business requirements:

    {reqs}

    Generate ONLY YAML (no markdown, no code blocks):
    user_stories:
      - id: US001
        title: ...
        description: ...
        acceptance_criteria: [...]
    api:
      - path: /todos
        method: GET
    db:
      tables:
        - name: Todo
          fields:
            - name: Id
              type: int
            - name: Title
              type: string
            - name: IsCompleted
              type: bool
    azure:
      resources:
        - name: todo-api
          type: ContainerApp
        - name: todo-frontend
          type: StaticWebApp

    CRITICAL CONSTRAINTS:
    - Write EVERYTHING in English (field names, descriptions, comments)
    - No emojis, no markdown fences
    - Clean YAML only
    """

    design_yaml = call_ai(
        prompt_design,
        system_content="You are a .NET/React/Azure architect. Generate clean YAML, no emojis, no markdown. Write EVERYTHING in English only."
    )
    print(design_yaml[:200])
    write_utf8("design.yaml", design_yaml)

    # 2) ARCHITECTURE DOCUMENTATION
    prompt_arch = f"""
    Based on this design YAML:

    {design_yaml}

    Write an architecture document in Markdown with sections:
    # Overview
    # Functional Requirements
    # Non-Functional Requirements
    # Logical Architecture
    # Physical Architecture (Azure: ACA, SWA, ACR, DB)
    # Main Flows
    # Security and Scalability

    Use simple Markdown (headings, lists), no code blocks.

    CRITICAL: Write EVERYTHING in English (all text, headings, descriptions).
    """

    arch_doc = call_ai(
        prompt_arch,
        system_content="You are a software architect writing clear documentation. Write EVERYTHING in English only."
    )
    write_utf8("docs/architecture.md", arch_doc)

    # 3) DB DESIGN PlantUML
    prompt_db = f"""
    Based on the following design YAML:

    {design_yaml}

    Generate an ER diagram in PlantUML syntax, ONLY PlantUML:

    @startuml
    entity Todo {{
      * Id : int
      --
      Title : string
      IsCompleted : bool
    }}
    @enduml

    CRITICAL: Use English for all entity names, field names, and comments.
    """

    db_puml = call_ai(
        prompt_db,
        system_content="You are a DBA drawing ER diagrams in PlantUML. Write EVERYTHING in English only."
    )
    write_utf8("docs/db_design.puml", db_puml)

    print("=== STEP1 completed (generated_app/design.yaml, docs, db_design.puml) ===")

if __name__ == "__main__":
    main()
