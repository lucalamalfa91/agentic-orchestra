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


@router.get("/github/login")
def github_login():
    """
    Get GitHub OAuth authorization URL.
    If GITHUB_CLIENT_ID not configured, returns fallback flag for gh CLI auth.

    Returns:
        Dictionary with authorization URL or fallback flag
    """
    client_id = os.getenv("GITHUB_CLIENT_ID", "").strip()

    if not client_id:
        # No OAuth App configured, use gh CLI token instead
        return {"url": None, "use_gh_cli": True, "message": "Using gh CLI authentication"}

    return {"url": github.get_authorization_url(), "use_gh_cli": False}


@router.get("/github/login-with-gh")
def github_login_with_gh(db: Session = Depends(get_db)):
    """
    Login using existing gh CLI authentication.
    Retrieves user info from gh CLI and creates/updates user in database.

    Returns:
        JWT token for authenticated user
    """
    try:
        import subprocess

        # Get authenticated user from gh CLI
        result = subprocess.run(
            ["gh", "api", "user", "-q", ".login,.id"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=401, detail="gh CLI not authenticated. Run: gh auth login")

        # Parse gh output (format: "username\nuser_id")
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            raise HTTPException(status_code=400, detail="Failed to get user info from gh CLI")

        username = lines[0]
        github_id = lines[1]

        # Get token from gh (scoped to this session)
        token_result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
        )

        if token_result.returncode != 0:
            raise HTTPException(status_code=401, detail="Failed to get GitHub token from gh CLI")

        github_token = token_result.stdout.strip()

        # Find or create user
        user = db.query(User).filter(User.github_id == str(github_id)).first()

        if not user:
            user = User(
                github_id=str(github_id),
                github_username=username,
                github_token=github_token,
            )
            db.add(user)
        else:
            # Update token
            user.github_token = github_token

        db.commit()
        db.refresh(user)

        # Generate JWT token
        jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "username": user.github_username,
                "exp": datetime.utcnow() + timedelta(days=7),
            },
            jwt_secret,
            algorithm="HS256",
        )

        return {"token": jwt_token, "user_id": user.id, "username": user.github_username}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=401, detail=f"gh CLI error: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


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

        # Generate JWT token
        jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
        jwt_token = jwt.encode(
            {
                "user_id": user.id,
                "username": user.github_username,
                "exp": datetime.utcnow() + timedelta(days=7),
            },
            jwt_secret,
            algorithm="HS256",
        )

        return {"token": jwt_token, "user_id": user.id, "username": user.github_username}

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
