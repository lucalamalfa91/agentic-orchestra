"""
Authentication API endpoints for OAuth integrations.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import jwt
import os
import requests
from datetime import datetime, timedelta

try:
    from orchestrator_ui.backend.oauth_handlers import github, vercel, railway
    from orchestrator_ui.backend.models import User, DeployProviderAuth
    from orchestrator_ui.backend.database import get_db
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from oauth_handlers import github, vercel, railway
    from models import User, DeployProviderAuth
    from database import get_db


router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "secret")


def create_jwt_token(user_id: int):
    """
    Create a JWT token for a user.

    Args:
        user_id: User ID to encode in the token

    Returns:
        Encoded JWT token string
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_jwt_token(token: str):
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("user_id")
    except:
        return None


def get_current_user_id(token: str = None):
    """
    Helper function to get the current user ID from a token.

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise
    """
    if not token:
        return None
    return verify_jwt_token(token)


@router.get("/github/login")
def github_login():
    """
    Get GitHub OAuth authorization URL.

    Returns:
        Dictionary with authorization URL
    """
    return {"url": github.get_authorization_url()}


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle GitHub OAuth callback.

    Args:
        code: Authorization code from GitHub
        db: Database session

    Returns:
        JWT token for authenticated user
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")

    try:
        # Exchange code for token
        token_data = github.exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")

        # Get user info from GitHub
        user_info = github.get_user_info(access_token)

        # Find or create user
        user = db.query(User).filter(User.github_id == str(user_info["id"])).first()

        if not user:
            user = User(
                github_id=str(user_info["id"]),
                github_username=user_info["login"],
                github_token=access_token,
            )
            db.add(user)
        else:
            # Update token in case it changed
            user.github_token = access_token

        db.commit()
        db.refresh(user)

        # Generate JWT token using the new helper function
        jwt_token = create_jwt_token(user.id)

        return {"token": jwt_token, "user_id": user.id}

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/github/status")
def github_status(user_id: int, db: Session = Depends(get_db)):
    """
    Check GitHub connection status for a user.

    Args:
        user_id: User ID to check
        db: Database session

    Returns:
        Connection status and username
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user = db.query(User).filter(User.id == user_id).first()

    return {
        "connected": user is not None,
        "username": user.github_username if user else None,
    }


@router.get("/deploy/{provider}/login")
def deploy_login(provider: str):
    """
    Get deployment provider OAuth authorization URL.

    Args:
        provider: Provider name (vercel or railway)

    Returns:
        Dictionary with authorization URL
    """
    handlers = {"vercel": vercel, "railway": railway}
    handler = handlers.get(provider)

    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    return {"url": handler.get_authorization_url()}


@router.get("/deploy/{provider}/callback")
def deploy_callback(provider: str, code: str, user_id: int, db: Session = Depends(get_db)):
    """
    Handle deployment provider OAuth callback.

    Args:
        provider: Provider name (vercel or railway)
        code: Authorization code
        user_id: User ID to associate with
        db: Database session

    Returns:
        Status confirmation
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    handlers = {"vercel": vercel, "railway": railway}
    handler = handlers.get(provider)

    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    try:
        # Exchange code for token
        token_data = handler.exchange_code_for_token(code)

        # Find or create auth record
        auth = (
            db.query(DeployProviderAuth)
            .filter(
                DeployProviderAuth.user_id == user_id,
                DeployProviderAuth.provider_name == provider,
            )
            .first()
        )

        if not auth:
            auth = DeployProviderAuth(user_id=user_id, provider_name=provider)

        # Update tokens
        auth.access_token = token_data.get("access_token", "")
        auth.refresh_token = token_data.get("refresh_token")

        db.add(auth)
        db.commit()

        return {"status": "ok", "provider": provider}

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"{provider} API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
