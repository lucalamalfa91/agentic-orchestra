# app-factory/AI_agents/backend_agent.py
from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP2: backend .NET ===")
    design = read_utf8("design.yaml")

    prompt = f"""
    Design YAML:

    {design}

    Write the COMPLETE content of Program.cs file for a .NET 8 Minimal API
    that exposes CRUD /todos with EF Core SQLite (DbContext TodoDb, entity Todo with Id, Title, IsCompleted).

    CRITICAL CONSTRAINTS:
    - DO NOT use markdown code blocks
    - DO NOT use language markers (no ```csharp, no ```)
    - Respond ONLY with C# code for Program.cs, ready to compile
    - Write ALL code, comments, variable names, strings in ENGLISH only
    - Use English for all entity names, properties, endpoints, error messages
    """

    program_cs = call_ai(
        prompt,
        system_content="You are a senior .NET backend engineer. Produce only valid C# code, no markdown. Write EVERYTHING in English only."
    )
    app_tsx = strip_markdown_fences(program_cs)
    write_utf8("backend/Program.cs", program_cs)

if __name__ == "__main__":
    main()
