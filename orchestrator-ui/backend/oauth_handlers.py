"""
OAuth handlers for GitHub, Vercel, and Railway integrations.
"""
import os
import requests
from typing import Dict


class OAuthHandler:
    """Base OAuth handler with common functionality."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, authorize_url: str, token_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.token_url = token_url

    def get_authorization_url(self) -> str:
        """Generate OAuth authorization URL."""
        return f"{self.authorize_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=repo"

    def exchange_code_for_token(self, code: str) -> Dict[str, str]:
        """Exchange authorization code for access token."""
        response = requests.post(
            self.token_url,
            headers={"Accept": "application/json"},
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


class GitHubOAuthHandler(OAuthHandler):
    """GitHub OAuth handler."""

    def __init__(self):
        super().__init__(
            client_id=os.getenv("GITHUB_CLIENT_ID", ""),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5173/auth/callback"),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
        )

    def get_user_info(self, access_token: str) -> Dict[str, any]:
        """Get GitHub user information."""
        response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


class VercelOAuthHandler(OAuthHandler):
    """Vercel OAuth handler."""

    def __init__(self):
        super().__init__(
            client_id=os.getenv("VERCEL_CLIENT_ID", ""),
            client_secret=os.getenv("VERCEL_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("VERCEL_REDIRECT_URI", "http://localhost:5173/auth/callback"),
            authorize_url="https://vercel.com/oauth/authorize",
            token_url="https://api.vercel.com/v2/oauth/access_token",
        )


class RailwayOAuthHandler(OAuthHandler):
    """Railway OAuth handler."""

    def __init__(self):
        super().__init__(
            client_id=os.getenv("RAILWAY_CLIENT_ID", ""),
            client_secret=os.getenv("RAILWAY_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("RAILWAY_REDIRECT_URI", "http://localhost:5173/auth/callback"),
            authorize_url="https://railway.app/oauth/authorize",
            token_url="https://railway.app/api/oauth/token",
        )


# Singleton instances
github = GitHubOAuthHandler()
vercel = VercelOAuthHandler()
railway = RailwayOAuthHandler()
