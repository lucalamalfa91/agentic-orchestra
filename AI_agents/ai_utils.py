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

APP_GEN_DIR = BASE_DIR / "app-generated" 

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
    relative_path è relativo a app-generated/, es: 'design.yaml',
    'backend/Program.cs', 'docs/architecture.md', ecc.
    """
    target = APP_GEN_DIR / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8", errors="ignore")
    with open(target, "wb") as f:
        f.write(data)
    print(f"✅ scritto {target}")

def read_utf8(relative_path):
    target = APP_GEN_DIR / relative_path
    with open(target, "r", encoding="utf-8") as f:
        return f.read()
