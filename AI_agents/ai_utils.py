# app-factory/AI_agents/ai_utils.py
import os
import requests
import re
from pathlib import Path
from dotenv import load_dotenv

# carica .env dalla root (app-factory)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BASE_URL = os.getenv("ADESSO_BASE_URL")
API_KEY = os.getenv("ADESSO_AI_HUB_KEY")
MODEL = "claude-haiku-4-5"

APP_GEN_DIR = BASE_DIR / "generated_app" 

def strip_markdown_fences(text: str) -> str:
    """
    Se la risposta è dentro ```lang ... ```, estrae solo il codice.
    Se ci sono più blocchi, prende il primo.
    Se non trova fence, restituisce il testo così com'è.
    """
    # match ```lang\n...code...\n``` (non greedy)
    m = re.search(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    # fallback: rimuovi eventuali ``` sparsi
    return re.sub(r"```", "", text).strip()

def call_ai(user_content, system_content="", max_tokens=4000):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    resp = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def write_utf8(relative_path, text):
    """
    relative_path è relativo a generated_app/, es: 'design.yaml',
    'backend/Program.cs', 'docs/architecture.md', ecc.
    """
    target = APP_GEN_DIR / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8", errors="ignore")
    with open(target, "wb") as f:
        f.write(data)
    print(f"OK scritto {target}")

def read_utf8(relative_path):
    target = APP_GEN_DIR / relative_path
    with open(target, "r", encoding="utf-8") as f:
        return f.read()

def write_readme():
    """
    Generates a Markdown document explaining the purpose and design
    of the AI Factory repository (not the generated app).
    """
    print("=== README.md - Repo docs ===")

    # BASE_DIR is already defined in ai_utils as root of app-factory
    docs_dir = BASE_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)
    target = BASE_DIR / "README.md"

    prompt = """
    Write a Markdown document that explains the purpose of this repository.

    Context:
    - This repo contains an AI factory that, given a text requirement
      (e.g., "Create a Todo App with authentication"), generates:
        - design and documentation
        - .NET backend code
        - React frontend code
        - GitHub Actions CI/CD pipeline
        - Azure DevOps backlog items

    The document MUST explain:
    - Why this repository exists (problem it solves)
    - Vision: automate the software lifecycle end-to-end
    - Overview of main components:
      - AI_agents/ folder (agent roles)
      - run_all_agents.py script (orchestrator)
      - generated_app/ folder (generated output)
    - How data flows from one agent to another (high-level, no technical details)
    - How it can be extended (new agents for security, testing, etc.)
    - Current limitations (requires human supervision, not magic)

    Suggested structure:
    # AI Factory Repository Overview

    ## Objective
    (why this repo exists)

    ## AI Factory Concept
    (describe the general concept: pipeline of collaborating agents)

    ## Main Repository Components
    (explain AI_agents/, run_all_agents.py, generated_app/)

    ## Execution Flow
    (textual, no diagram needed, just clear description of steps)

    ## Possible Extensions
    (how to add new agents or adapt the flow)

    ## When to Use and When Not to Use
    (ideal use context, what it is NOT)

    Use clean Markdown (headings, paragraphs, lists), no code blocks
    with language indicators. No source code examples, only text.

    CRITICAL: Write EVERYTHING in English - all text, headings, descriptions.
    """

    raw_doc = call_ai(
        prompt,
        system_content="You are a software architect documenting the vision and structure of an AI factory repository. Write in English only."
    )

    # no strip_markdown_fences here, we want pure Markdown doc
    text = raw_doc.encode("utf-8", errors="ignore")
    with open(target, "wb") as f:
        f.write(text)

    print(f"OK Written {target}")
