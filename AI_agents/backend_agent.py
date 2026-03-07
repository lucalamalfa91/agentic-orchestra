# app-factory/AI_agents/backend_agent.py
from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP2: backend .NET ===")
    design = read_utf8("design.yaml")

    prompt = f"""
    Design YAML:

    {design}

    Scrivi il contenuto COMPLETO del file Program.cs per una .NET 8 Minimal API
    che espone CRUD /todos con EF Core SQLite (DbContext TodoDb, entity Todo con Id, Title, IsCompleted).

    Vincoli IMPORTANTI:
    - NON usare blocchi di codice markdown.
    - NON usare marcatori di linguaggio (niente ```csharp, niente ```).
    - Rispondi SOLO con codice C# di Program.cs, pronto da compilare.
    """

    program_cs = call_ai(
        prompt,
        system_content="Sei un senior .NET backend engineer. Produci solo codice C# valido, senza markdown."
    )
    app_tsx = strip_markdown_fences(program_cs)
    write_utf8("backend/Program.cs", program_cs)

if __name__ == "__main__":
    main()
