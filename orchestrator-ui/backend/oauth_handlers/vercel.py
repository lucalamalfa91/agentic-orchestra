import os
import requests


def get_authorization_url():
    """Generate Vercel OAuth authorization URL."""
    client_id = os.getenv("VERCEL_CLIENT_ID")
    callback_url = os.getenv("VERCEL_CALLBACK_URL", "http://localhost:5173/auth/callback/vercel")
    return f"https://vercel.com/integrations/authorize?client_id={client_id}&redirect_uri={callback_url}"


def exchange_code_for_token(code: str):
    """Exchange authorization code for access token."""
    client_id = os.getenv("VERCEL_CLIENT_ID")
    client_secret = os.getenv("VERCEL_CLIENT_SECRET")
    resp = requests.post("https://api.vercel.com/v1/oauth/access_token", json={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": os.getenv("VERCEL_CALLBACK_URL")
    })
    return resp.json()
