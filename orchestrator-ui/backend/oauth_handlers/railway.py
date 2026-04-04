import os
import requests


def get_authorization_url():
    """Generate Railway OAuth authorization URL."""
    client_id = os.getenv("RAILWAY_CLIENT_ID")
    callback_url = os.getenv("RAILWAY_CALLBACK_URL", "http://localhost:5173/auth/callback/railway")
    return f"https://railway.app/oauth/authorize?client_id={client_id}&redirect_uri={callback_url}&response_type=code"


def exchange_code_for_token(code: str):
    """Exchange authorization code for access token."""
    client_id = os.getenv("RAILWAY_CLIENT_ID")
    client_secret = os.getenv("RAILWAY_CLIENT_SECRET")
    resp = requests.post("https://railway.app/oauth/token", json={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": os.getenv("RAILWAY_CALLBACK_URL")
    })
    return resp.json()
