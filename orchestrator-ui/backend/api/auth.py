"""
Authentication API endpoints for OAuth integrations.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import jwt
import os
import requests
from datetime import datetime, timedelta

try:
    from orchestrator_ui.backend.oauth_handlers import github, vercel, railway
    from orchestrator_ui.backend.models import User, DeployProviderAuth, Configuration
    from orchestrator_ui.backend.database import get_db
    from orchestrator_ui.backend.encryption_service import encrypt
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from oauth_handlers import github, vercel, railway
    from models import User, DeployProviderAuth, Configuration
    from database import get_db
    from encryption_service import encrypt


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/github/check-gh")
def check_gh_auth():
    """
    Check if gh CLI is authenticated.

    Returns:
        {"authenticated": true/false}
    """
    try:
        import subprocess
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        return {"authenticated": result.returncode == 0}
    except Exception:
        return {"authenticated": False}


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
            # Extract meaningful error from stderr
            error_msg = result.stderr.strip() if result.stderr else "gh CLI not authenticated"
            raise HTTPException(
                status_code=401,
                detail=f"gh CLI authentication failed: {error_msg}. Please run 'gh auth login' or 'gh auth refresh'"
            )

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

        # Auto-configure AI provider from environment variables if not already configured
        ai_base_url = os.getenv("ADESSO_BASE_URL", "").strip()
        ai_api_key = os.getenv("ADESSO_AI_HUB_KEY", "").strip()

        if ai_base_url and ai_api_key:
            # Use raw SQL to bypass SQLAlchemy metadata cache issue
            from sqlalchemy import text
            config_result = db.execute(
                text("SELECT id FROM configurations WHERE user_id = :user_id LIMIT 1"),
                {"user_id": user.id}
            ).fetchone()

            if not config_result:
                # Create new config using raw SQL
                db.execute(
                    text("INSERT INTO configurations (user_id, ai_base_url, ai_api_key_encrypted, ai_provider, is_active) VALUES (:user_id, :base_url, :api_key, 'custom', 1)"),
                    {"user_id": user.id, "base_url": ai_base_url, "api_key": encrypt(ai_api_key)}
                )
            else:
                # Update existing config
                db.execute(
                    text("UPDATE configurations SET is_active = 1 WHERE user_id = :user_id"),
                    {"user_id": user.id}
                )
            db.commit()

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
        import traceback
        print(f"ERROR in login-with-gh: {e}")
        print(traceback.format_exc())
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


@router.post("/github/device-flow/start")
def start_device_flow():
    """
    Start GitHub Device Flow authentication using GitHub REST API.
    No gh CLI required!

    Returns device_code, user_code, and verification_uri.
    """
    try:
        # GitHub CLI's public client_id for device flow
        # This is public and safe to use - it's in gh CLI source code
        client_id = "178c6fc778ccc68e1d6a"

        # Start device flow with GitHub API
        response = requests.post(
            "https://github.com/login/device/code",
            headers={
                "Accept": "application/json",
            },
            json={
                "client_id": client_id,
                "scope": "repo read:org gist"
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub API error: {response.text}"
            )

        data = response.json()

        return {
            "device_code": data["device_code"],
            "user_code": data["user_code"],
            "verification_uri": data["verification_uri"],
            "expires_in": data["expires_in"],
            "interval": data.get("interval", 5)
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"GitHub API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start device flow: {str(e)}")


class DeviceFlowPollRequest(BaseModel):
    device_code: str


@router.post("/github/device-flow/poll")
def poll_device_flow(request: DeviceFlowPollRequest, db: Session = Depends(get_db)):
    """
    Poll to check if device flow authentication is complete.
    Returns JWT token if authentication succeeded.

    Args:
        device_code: The device_code from start_device_flow
    """
    try:
        client_id = "178c6fc778ccc68e1d6a"

        # Poll GitHub for access token
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "Accept": "application/json",
            },
            json={
                "client_id": client_id,
                "device_code": request.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        )

        if response.status_code != 200:
            return {"status": "error", "message": f"GitHub API error: {response.status_code}"}

        data = response.json()

        # Debug logging
        print(f"[POLL] GitHub response: {data}")

        # Check for errors
        if "error" in data:
            error_code = data["error"]
            print(f"[POLL] Error from GitHub: {error_code}")
            if error_code == "authorization_pending":
                return {"status": "pending", "message": "Waiting for authorization..."}
            elif error_code == "slow_down":
                # GitHub wants us to slow down - return new interval
                new_interval = data.get("interval", 5)
                return {
                    "status": "pending",
                    "message": "Polling too fast, slowing down...",
                    "interval": new_interval
                }
            elif error_code == "expired_token":
                return {"status": "error", "message": "Code expired. Please try again."}
            elif error_code == "access_denied":
                return {"status": "error", "message": "Access denied by user."}
            else:
                return {"status": "error", "message": f"GitHub error: {error_code}"}

        # Success! Got access token
        github_token = data["access_token"]
        print(f"[POLL] SUCCESS! Got access token, creating session...")

        # Get user info from GitHub API
        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get user info from GitHub")

        user_data = user_response.json()
        username = user_data["login"]
        github_id = str(user_data["id"])

        # Create or update user in database
        user = db.query(User).filter(User.github_id == str(github_id)).first()

        if not user:
            user = User(
                github_id=str(github_id),
                github_username=username,
                github_token=github_token,
            )
            db.add(user)
        else:
            user.github_token = github_token

        db.commit()
        db.refresh(user)

        # Auto-configure AI provider from env vars if available
        ai_base_url = os.getenv("ADESSO_BASE_URL", "").strip()
        ai_api_key = os.getenv("ADESSO_AI_HUB_KEY", "").strip()

        if ai_base_url and ai_api_key:
            # Note: Using raw SQL to bypass SQLAlchemy metadata cache issue
            from sqlalchemy import text
            config_result = db.execute(
                text("SELECT id FROM configurations WHERE user_id = :user_id LIMIT 1"),
                {"user_id": user.id}
            ).fetchone()

            if not config_result:
                # Create new config using raw SQL
                db.execute(
                    text("INSERT INTO configurations (user_id, ai_base_url, ai_api_key_encrypted, ai_provider, is_active) VALUES (:user_id, :base_url, :api_key, 'custom', 1)"),
                    {"user_id": user.id, "base_url": ai_base_url, "api_key": encrypt(ai_api_key)}
                )
            else:
                # Update existing config
                db.execute(
                    text("UPDATE configurations SET is_active = 1 WHERE user_id = :user_id"),
                    {"user_id": user.id}
                )
            db.commit()

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

        return {
            "status": "complete",
            "token": jwt_token,
            "user_id": user.id,
            "username": user.github_username
        }

    except Exception as e:
        import traceback
        print(f"ERROR in poll_device_flow: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}


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
