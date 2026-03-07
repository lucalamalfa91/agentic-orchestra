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
    print(f"✅ scritto {target}")

def read_utf8(relative_path):
    target = APP_GEN_DIR / relative_path
    with open(target, "r", encoding="utf-8") as f:
        return f.read()

def write_readme():
    """
    Genera un documento Markdown che spiega il senso e il design
    della repository AI Factory (non dell'app generata).
    """
    print("=== README.md - Repo docs ===")

    # BASE_DIR è già definita in ai_utils come root di app-factory
    docs_dir = BASE_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)
    target = BASE_DIR / "README.md"

    prompt = """
    Scrivi un documento Markdown che spiega il senso di questa repository.

    Contesto:
    - La repo contiene una AI factory che, dato un requisito testuale
      (es. "Crea una Todo App con autenticazione"), genera:
        - design e documentazione
        - codice backend .NET
        - codice frontend React
        - pipeline CI/CD GitHub Actions
        - backlog items su Azure DevOps

    Il documento DEVE spiegare:
    - Perché esiste questa repository (problema che risolve)
    - Visione: automatizzare il ciclo di vita software end-to-end
    - Panoramica dei componenti principali:
      - cartella AI_agents/ (ruolo degli agent)
      - script run_all_agents.py (orchestratore)
      - cartella app-generated/ (output generato)
    - Come fluiscono i dati da un agent all'altro (alto livello, senza dettagli tecnici)
    - Come può essere estesa (nuovi agent per security, test, ecc.)
    - Limiti attuali (serve supervisione umana, non è magia)

    Struttura suggerita:
    # AI Factory Repository Overview

    ## Obiettivo
    (perché esiste questa repo)

    ## Concetto di AI Factory
    (descrivi il concetto generale: pipeline di agent che collaborano)

    ## Componenti principali della repository
    (spiega AI_agents/, run_all_agents.py, app-generated/)

    ## Flusso di esecuzione
    (testuale, non serve diagramma, basta descrizione chiara dei passi)

    ## Estensioni possibili
    (come aggiungere nuovi agent o adattare il flusso)

    ## Quando usarla e quando no
    (contesto d'uso ideale, cosa NON è)

    Usa Markdown pulito (titoli, paragrafi, liste), nessun blocco di codice
    con indicazione di linguaggio. Niente esempi di codice sorgente, solo testo.
    """

    raw_doc = call_ai(
        prompt,
        system_content="Sei un software architect che documenta la visione e la struttura di una repository AI factory."
    )

    # qui niente strip_markdown_fences, vogliamo proprio un doc Markdown
    text = raw_doc.encode("utf-8", errors="ignore")
    with open(target, "wb") as f:
        f.write(text)

    print(f"✅ scritto {target}")
