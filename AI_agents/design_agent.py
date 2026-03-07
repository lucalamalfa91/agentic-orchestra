# app-factory/AI_agents/design_agent.py
from .ai_utils import call_ai, write_utf8

def main():
    print("=== STEP1: design + architettura + DB ===")

    reqs = """
    Todo App semplice:
    - FE: React + Tailwind (add/edit/delete/toggle todos)
    - BE: .NET 8 Minimal API + EF Core SQLite (/todos CRUD)
    - Deploy: Azure Container Apps (BE) + Static Web App (FE)
    - ACR: crsharedacrcorchn001
    - Test: xUnit/Jest
    """

    # 1) DESIGN YAML
    prompt_design = f"""
    Requisiti business:

    {reqs}

    Genera SOLO YAML (nessun markdown, nessun blocco di codice):
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
    """

    design_yaml = call_ai(
        prompt_design,
        system_content="Sei un architect .NET/React/Azure. YAML pulito, senza emoji e senza markdown."
    )
    print(design_yaml[:200])
    write_utf8("design.yaml", design_yaml)

    # 2) DOCUMENTAZIONE ARCHITETTURALE
    prompt_arch = f"""
    A partire da questo design YAML:

    {design_yaml}

    Scrivi un documento di architettura in Markdown con sezioni:
    # Panoramica
    # Requisiti funzionali
    # Requisiti non funzionali
    # Architettura logica
    # Architettura fisica (Azure: ACA, SWA, ACR, DB)
    # Flussi principali
    # Sicurezza e scalabilità

    Usa Markdown semplice (titoli, liste), niente blocchi di codice.
    """

    arch_doc = call_ai(prompt_arch, system_content="Sei un architect software, documentazione chiara.")
    write_utf8("docs/architecture.md", arch_doc)

    # 3) DISEGNO DB PlantUML
    prompt_db = f"""
    Sulla base del seguente design YAML:

    {design_yaml}

    Genera un diagramma ER in sintassi PlantUML, SOLO PlantUML:

    @startuml
    entity Todo {{
      * Id : int
      --
      Title : string
      IsCompleted : bool
    }}
    @enduml
    """

    db_puml = call_ai(prompt_db, system_content="Sei un DBA che disegna ER diagram in PlantUML.")
    write_utf8("docs/db_design.puml", db_puml)

    print("=== STEP1 completato (app-generated/design.yaml, docs, db_design.puml) ===")

if __name__ == "__main__":
    main()
