# app-factory/AI_agents/ai_utils.py
import os
import requests
import re
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

MODEL = "claude-haiku-4-5"
APP_GEN_DIR = BASE_DIR / "generated_app"


def strip_markdown_fences(text: str) -> str:
    m = re.search(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return re.sub(r"```", "", text).strip()


def call_ai(user_content, system_content="", max_tokens=4000):
    base_url = os.getenv("ADESSO_BASE_URL")
    api_key  = os.getenv("ADESSO_AI_HUB_KEY")

    # ── diagnostic block (remove once auth works) ──────────────────────
    masked_key = (
        f"{api_key[:6]}...{api_key[-4:]}" if api_key and len(api_key) > 10
        else repr(api_key)
    )
    print(f"[AI_UTILS] ADESSO_BASE_URL  = {base_url!r}")
    print(f"[AI_UTILS] ADESSO_AI_HUB_KEY= {masked_key}  (len={len(api_key) if api_key else 0})")
    # ───────────────────────────────────────────────────────────────────

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

    # ── print full error body before raising ───────────────────────────
    if not resp.ok:
        print(f"[AI_UTILS] HTTP {resp.status_code} — response body: {resp.text[:500]}")
    # ───────────────────────────────────────────────────────────────────

    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def write_utf8(relative_path, text):
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
    ## AI Factory Concept
    ## Main Repository Components
    ## Execution Flow
    ## Possible Extensions
    ## When to Use and When Not to Use

    Use clean Markdown, no code blocks. Write EVERYTHING in English.
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
