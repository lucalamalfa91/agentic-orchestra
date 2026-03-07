from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP3: frontend React ===")
    design = read_utf8("design.yaml")

    prompt = f"""
    API design:

    {design}

    Scrivi il contenuto COMPLETO del file App.tsx (React 18 + TypeScript) per una todo app:

    - mostra lista todo
    - permette add/toggle/delete
    - chiama GET/POST/PUT/DELETE /todos via fetch

    Vincoli IMPORTANTI:
    - NON usare blocchi di codice markdown.
    - NON usare marcatori di linguaggio (niente ```typescript, niente ```).
    - Rispondi SOLO con codice TSX valido per App.tsx, pronto da usare in un progetto Vite React.
    - Se per errore usi ancora i triple backtick, il chiamante rimuoverà il blocco markdown e userà solo il contenuto interno.
    - usa tutti i comandi necessari per far compilare il codice
    """

    raw = call_ai(
        prompt,
        system_content="Sei un frontend engineer React 18/TypeScript. Produci solo codice TSX, niente markdown."
    )

    app_tsx = strip_markdown_fences(raw)
    write_utf8("frontend/App.tsx", app_tsx)

if __name__ == "__main__":
    main()
