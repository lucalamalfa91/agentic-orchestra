import os
from dotenv import load_dotenv

def get_ai_config():
    # Try database first if available
    try:
        from orchestrator_ui.backend.models import Configuration
        from orchestrator_ui.backend.database import SessionLocal
        db = SessionLocal()
        config = db.query(Configuration).filter(Configuration.is_active == True).first()
        if config:
            from orchestrator_ui.backend.encryption_service import decrypt
            return config.ai_base_url, decrypt(config.ai_api_key_encrypted)
    except:
        pass

    # Fallback to .env (backward compatible)
    load_dotenv()
    base_url = os.getenv("AI_BASE_URL") or os.getenv("ADESSO_BASE_URL")
    api_key = os.getenv("AI_API_KEY") or os.getenv("ADESSO_AI_HUB_KEY")
    return base_url, api_key
