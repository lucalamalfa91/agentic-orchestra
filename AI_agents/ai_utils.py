# app-factory/AI_agents/ai_utils.py
import os
import requests
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root as fallback.
# load_dotenv does NOT overwrite variables already present in the environment,
# so values injected by the orchestrator always take precedence.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

MODEL = "claude-haiku-4-5"
APP_GEN_DIR = BASE_DIR / "generated_app"


def strip_markdown_fences(text: str) -> str:
    """
    If the response is wrapped in ```lang ... ```, extract only the code.
    If multiple blocks exist, take the first.
    If no fence is found, return the text as-is.
    """
    m = re.search(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return re.sub(r"```", "", text).strip()


def call_ai(user_content, system_content="", max_tokens=4000):
    # Read at call-time so values injected by the orchestrator are always used.
    base_url = os.getenv("ADESSO_BASE_URL")
    api_key  = os.getenv("ADESSO_AI_HUB_KEY")

    if not base_url:
        raise ValueError(
            "ADESSO_BASE_URL is not set. "
            "Configure it in the UI (AI Configuration) or add it to .env"
        )
    if not api_key:
        raise ValueError(
            "ADESSO_AI_HUB_KEY is not set. "
            "Configure it in the UI (AI Configuration) or add it to .env"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user",   "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def write_utf8(relative_path, text):
    """
    relative_path is relative to generated_app/, e.g. 'design.yaml',
    'backend/Program.cs', 'docs/architecture.md', etc.
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
        system_content=(
            "You are a software architect documenting the vision and structure "
            "of an AI factory repository. Write in English only."
        ),
    )

    text = raw_doc.encode("utf-8", errors="ignore")
    with open(target, "wb") as f:
        f.write(text)

    print(f"OK Written {target}")
