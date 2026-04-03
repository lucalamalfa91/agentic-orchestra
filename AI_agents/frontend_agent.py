from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP3: frontend React ===")
    design = read_utf8("design.yaml")

    prompt = f"""
    API design:

    {design}

    Write the COMPLETE content of App.tsx file (React 18 + TypeScript) for a todo app:

    - display todo list
    - allow add/toggle/delete
    - call GET/POST/PUT/DELETE /todos via fetch

    CRITICAL CONSTRAINTS:
    - DO NOT use markdown code blocks
    - DO NOT use language markers (no ```typescript, no ```)
    - Respond ONLY with valid TSX code for App.tsx, ready to use in a Vite React project
    - If you accidentally use triple backticks, the caller will remove the markdown block and use only the inner content
    - Use all necessary imports to make the code compile
    - Write ALL code, comments, variable names, strings, UI text in ENGLISH only
    - Use English for all button labels, placeholders, error messages, UI text
    """

    raw = call_ai(
        prompt,
        system_content="You are a React 18/TypeScript frontend engineer. Produce only TSX code, no markdown. Write EVERYTHING in English only."
    )

    app_tsx = strip_markdown_fences(raw)
    write_utf8("frontend/App.tsx", app_tsx)

if __name__ == "__main__":
    main()
