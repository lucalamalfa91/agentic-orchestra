"""
Configuration API endpoints for AI provider settings.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests

try:
    from orchestrator_ui.backend.models import Configuration
    from orchestrator_ui.backend.database import get_db
    from orchestrator_ui.backend.encryption_service import encrypt, decrypt
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models import Configuration
    from database import get_db
    from encryption_service import encrypt, decrypt


router = APIRouter(prefix="/api/config", tags=["config"])


# Pydantic models for request validation
class AIProviderConfig(BaseModel):
    """AI provider configuration request."""
    user_id: int
    base_url: str
    api_key: str
    ai_provider: str = "openai"  # "openai" or "anthropic"


class AIProviderTest(BaseModel):
    """AI provider test request."""
    base_url: str
    api_key: str
    ai_provider: str = "openai"  # "openai", "anthropic", or "custom"


@router.post("/ai-provider")
def save_ai_provider(config_data: AIProviderConfig, db: Session = Depends(get_db)):
    """
    Save AI provider configuration for a user.

    Args:
        config_data: AI provider configuration data
        db: Database session

    Returns:
        Status confirmation
    """
    if not config_data.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    if not config_data.base_url:
        raise HTTPException(status_code=400, detail="Base URL is required")
    if not config_data.api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        # Find existing configuration
        config = db.query(Configuration).filter(Configuration.user_id == config_data.user_id).first()

        if not config:
            # Create new configuration
            config = Configuration(
                user_id=config_data.user_id,
                ai_base_url=config_data.base_url,
                ai_api_key_encrypted=encrypt(config_data.api_key),
                ai_provider=config_data.ai_provider,
                is_active=True,
            )
        else:
            # Update existing configuration
            config.ai_base_url = config_data.base_url
            config.ai_api_key_encrypted = encrypt(config_data.api_key)
            config.ai_provider = config_data.ai_provider
            config.is_active = True

        db.add(config)
        db.commit()

        return {"status": "saved", "user_id": config_data.user_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Encryption error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.get("/ai-provider")
def get_ai_provider(user_id: int, db: Session = Depends(get_db)):
    """
    Get AI provider configuration for a user.

    Args:
        user_id: User ID to retrieve configuration for
        db: Database session

    Returns:
        AI provider base URL (API key is not returned for security)
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    config = db.query(Configuration).filter(Configuration.user_id == user_id).first()

    if not config:
        return {"base_url": None, "ai_provider": "openai", "configured": False}

    return {
        "base_url": config.ai_base_url,
        "ai_provider": getattr(config, 'ai_provider', 'openai'),  # Graceful fallback for older DBs
        "configured": True
    }


@router.post("/ai-provider/test")
def test_ai_provider(test_data: AIProviderTest):
    """
    Test AI provider connection and credentials.

    Args:
        test_data: Test configuration data

    Returns:
        Success status
    """
    if not test_data.base_url:
        raise HTTPException(status_code=400, detail="Base URL is required")
    if not test_data.api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        if test_data.ai_provider == "anthropic":
            # Test Anthropic API
            headers = {
                "x-api-key": test_data.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            payload = {
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            url = f"{test_data.base_url.rstrip('/')}/v1/messages"

        else:
            # Test OpenAI or Custom (OpenAI-compatible)
            headers = {
                "Authorization": f"Bearer {test_data.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10,
            }
            url = f"{test_data.base_url.rstrip('/')}/chat/completions"

        # Attempt to call the AI provider
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        # Consider 200-299 as success
        success = 200 <= response.status_code < 300

        if not success:
            # Include error details for debugging
            try:
                error_detail = response.json()
                error_msg = error_detail.get('error', {}).get('message', response.text[:200])
            except:
                error_msg = response.text[:200]

            return {
                "success": False,
                "status_code": response.status_code,
                "message": f"Failed: {error_msg}",
            }

        return {
            "success": True,
            "status_code": response.status_code,
            "message": "✓ Connection successful! API key is valid.",
        }

    except requests.Timeout:
        return {"success": False, "message": "Request timeout - provider is not responding"}
    except requests.ConnectionError:
        return {"success": False, "message": "Connection error - cannot reach provider"}
    except Exception as e:
        return {"success": False, "message": f"Test failed: {str(e)}"}
