from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences, APP_GEN_DIR
import shutil
import json

def main():
    print("=== STEP3: frontend React + Design System ===")
    design = read_utf8("design.yaml")

    # Load UX/UI design system
    try:
        uxui_design_raw = read_utf8("uxui_design.json")
        uxui_design = json.loads(uxui_design_raw)
        print(f"OK UX/UI design system loaded")
        has_design_system = True
    except FileNotFoundError:
        print("WARNING UX/UI design system not found, proceeding without it")
        uxui_design = {}
        uxui_design_raw = "{}"
        has_design_system = False
    except json.JSONDecodeError:
        print("WARNING UX/UI design system is invalid JSON, proceeding without it")
        uxui_design = {}
        uxui_design_raw = "{}"
        has_design_system = False

    # 1) Generate App.tsx with design system integration
    prompt = f"""
    API design:

    {design}

    DESIGN SYSTEM (apply all styles from this):

    {uxui_design_raw}

    Write the COMPLETE content of App.tsx file (React 18 + TypeScript) for a todo app:

    - display todo list
    - allow add/toggle/delete
    - call GET/POST/PUT/DELETE /todos via fetch

    DESIGN SYSTEM APPLICATION REQUIREMENTS:
    1. Import design tokens: import DESIGN_SYSTEM from './uxui_design.json'
    2. Apply colors from design_tokens.colors (primary gradients, dark backgrounds)
    3. Use design_tokens.typography (Geist for headings, Inter for body)
    4. Apply design_tokens.spacing for padding/margins
    5. Implement animations from design_tokens.animations (fadeIn, slideUp, scaleIn)
    6. Use glassmorphism effects from design_tokens.effects
    7. Apply component styles from components section (buttons primary variant with gradient)
    8. Make it BEAUTIFUL, MODERN, and PRODUCTION-READY
    9. Use inline CSS-in-JS styles or CSS modules with design tokens
    10. Implement micro-interactions: hover effects (transform: translateY), smooth transitions

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
        system_content="You are an expert React 18/TypeScript frontend engineer specializing in design system implementation. Produce only TSX code, no markdown. Create beautiful, modern UIs. Write EVERYTHING in English only.",
        max_tokens=6000
    )

    app_tsx = strip_markdown_fences(raw)
    write_utf8("frontend/App.tsx", app_tsx)

    # 2) Generate index.css with design tokens and global styles
    if has_design_system:
        prompt_css = f"""
Based on this design system:

{uxui_design_raw}

Generate a complete index.css file with:
1. CSS custom properties (variables) for all design tokens:
   - Colors: --color-primary, --color-accent, --color-background, etc.
   - Typography: --font-heading, --font-body, --font-size-*, --font-weight-*
   - Spacing: --spacing-xs, --spacing-sm, --spacing-md, etc.
   - Shadows: --shadow-sm, --shadow-md, --shadow-lg, --shadow-glow
   - Border radius: --radius-sm, --radius-md, --radius-lg, --radius-full

2. Global styles:
   - * {{
       margin: 0;
       padding: 0;
       box-sizing: border-box;
     }}
   - html, body {{ background: var(--color-background); color: var(--color-text); font-family: var(--font-body); }}
   - Heading styles (h1-h6) with var(--font-heading)

3. Utility classes:
   - .glass-card {{backdrop-filter: blur(20px); background: var(--color-glass); border: 1px solid var(--color-glass-border);}}
   - .glass-header {{similar to glass-card}}
   - .gradient-primary {{background: linear-gradient(135deg, #667eea, #764ba2);}}

4. Animation keyframes:
   - @keyframes fadeIn {{ 0% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
   - @keyframes slideUp {{ 0% {{ opacity: 0; transform: translateY(20px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
   - @keyframes scaleIn {{ 0% {{ opacity: 0; transform: scale(0.95); }} 100% {{ opacity: 1; transform: scale(1); }} }}
   - @keyframes shimmer {{ 0% {{ background-position: -1000px 0; }} 100% {{ background-position: 1000px 0; }} }}

5. Import font declarations for Geist and Inter (or fallbacks)

Output ONLY CSS, no markdown, no code blocks, no explanations.
Write everything in English.
"""

        css_raw = call_ai(
            prompt_css,
            system_content="You are a CSS expert. Output only pure CSS, no markdown, no explanations. Write in English only.",
            max_tokens=4000
        )

        index_css = strip_markdown_fences(css_raw)
        write_utf8("frontend/src/index.css", index_css)
        print(f"OK Generated index.css with design tokens ({len(index_css)} chars)")

    # 3) Copy uxui_design.json to frontend source
    try:
        uxui_source = APP_GEN_DIR / "uxui_design.json"
        uxui_dest = APP_GEN_DIR / "frontend" / "src" / "uxui_design.json"
        uxui_dest.parent.mkdir(parents=True, exist_ok=True)
        if uxui_source.exists():
            shutil.copy(uxui_source, uxui_dest)
            print(f"OK Copied uxui_design.json to frontend/src/")
    except Exception as e:
        print(f"WARNING Could not copy uxui_design.json: {str(e)}")

if __name__ == "__main__":
    main()
