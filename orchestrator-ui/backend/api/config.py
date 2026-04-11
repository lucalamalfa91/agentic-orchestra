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


@router.options("/ai-provider")
async def options_ai_provider():
    """CORS preflight for ai-provider endpoint."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


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
        print(f"[SAVE CONFIG] user_id={config_data.user_id}, provider={config_data.ai_provider}, base_url={config_data.base_url}")

        # Find existing configuration
        config = db.query(Configuration).filter(Configuration.user_id == config_data.user_id).first()

        if not config:
            # Create new configuration
            print(f"[SAVE CONFIG] Creating NEW configuration for user {config_data.user_id}")
            config = Configuration(
                user_id=config_data.user_id,
                ai_base_url=config_data.base_url,
                ai_api_key_encrypted=encrypt(config_data.api_key),
                ai_provider=config_data.ai_provider,
                is_active=True,
            )
        else:
            # Update existing configuration
            print(f"[SAVE CONFIG] Updating EXISTING configuration (id={config.id}) for user {config_data.user_id}")
            config.ai_base_url = config_data.base_url
            config.ai_api_key_encrypted = encrypt(config_data.api_key)
            config.ai_provider = config_data.ai_provider
            config.is_active = True

        db.add(config)
        db.commit()
        db.refresh(config)

        print(f"[SAVE CONFIG] ✓ Configuration saved successfully (id={config.id})")
        return {"status": "saved", "user_id": config_data.user_id, "config_id": config.id}

    except ValueError as e:
        print(f"[SAVE CONFIG] ✗ Encryption error: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Encryption error: {str(e)}")
    except Exception as e:
        print(f"[SAVE CONFIG] ✗ Failed to save: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
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


@router.get("/ai-provider/test-current")
def test_current_ai_provider(user_id: int, db: Session = Depends(get_db)):
    """
    Test the currently configured AI provider for a user.

    This endpoint reads the user's saved configuration from the database,
    decrypts the API key, and tests the connection.

    Args:
        user_id: User ID to test configuration for
        db: Database session

    Returns:
        Success status with detailed error messages if failed
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    print(f"[TEST CURRENT] Testing AI config for user_id={user_id}")

    # Get user's active configuration
    config = db.query(Configuration).filter(
        Configuration.user_id == user_id,
        Configuration.is_active == True
    ).first()

    if not config:
        print(f"[TEST CURRENT] ✗ No active configuration found for user {user_id}")
        return {
            "success": False,
            "message": "No AI provider configured. Please save your settings first."
        }

    # Decrypt API key
    try:
        api_key = decrypt(config.ai_api_key_encrypted)
        if not api_key or len(api_key) < 10:
            raise ValueError("Invalid or empty API key")
        print(f"[TEST CURRENT] ✓ Successfully decrypted API key (length: {len(api_key)})")
    except Exception as e:
        print(f"[TEST CURRENT] ✗ Failed to decrypt API key: {e}")
        return {
            "success": False,
            "message": f"Failed to decrypt API key: {str(e)}. Please re-save your configuration."
        }

    # Get provider (with fallback for older DBs)
    ai_provider = getattr(config, 'ai_provider', 'openai')
    base_url = config.ai_base_url

    print(f"[TEST CURRENT] Testing provider={ai_provider}, base_url={base_url}")

    # Test connection using the same logic as /ai-provider/test
    try:
        if ai_provider == "anthropic":
            # Test Anthropic API
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            payload = {
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            url = f"{base_url.rstrip('/')}/v1/messages"
            print(f"[TEST CURRENT] Anthropic test URL: {url}")

        else:
            # Test OpenAI or Custom (OpenAI-compatible)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10,
            }
            url = f"{base_url.rstrip('/')}/chat/completions"
            print(f"[TEST CURRENT] OpenAI/Custom test URL: {url}")

        # Attempt to call the AI provider
        print(f"[TEST CURRENT] Sending request...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"[TEST CURRENT] Response status: {response.status_code}")

        # Consider 200-299 as success
        success = 200 <= response.status_code < 300

        if not success:
            # Include error details for debugging
            try:
                error_detail = response.json()
                error_msg = error_detail.get('error', {}).get('message', response.text[:200])
            except:
                error_msg = response.text[:200]

            print(f"[TEST CURRENT] ✗ Test failed: {error_msg}")
            return {
                "success": False,
                "status_code": response.status_code,
                "message": f"Connection failed: {error_msg}",
                "provider": ai_provider,
                "base_url": base_url
            }

        print(f"[TEST CURRENT] ✓ Test successful!")
        return {
            "success": True,
            "status_code": response.status_code,
            "message": "✓ Connection successful! Your AI provider is working correctly.",
            "provider": ai_provider,
            "base_url": base_url
        }

    except requests.Timeout:
        print(f"[TEST CURRENT] ✗ Request timeout")
        return {
            "success": False,
            "message": f"Request timeout - {base_url} is not responding",
            "provider": ai_provider,
            "base_url": base_url
        }
    except requests.ConnectionError:
        print(f"[TEST CURRENT] ✗ Connection error")
        return {
            "success": False,
            "message": f"Connection error - cannot reach {base_url}",
            "provider": ai_provider,
            "base_url": base_url
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[TEST CURRENT] ✗ Unexpected error: {e}")
        print(f"[TEST CURRENT] Traceback:\n{tb}")
        return {
            "success": False,
            "message": f"Test failed: {str(e)}",
            "provider": ai_provider,
            "base_url": base_url
        }
