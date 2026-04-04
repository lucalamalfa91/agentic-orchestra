import os
import requests


def get_authorization_url():
    """Generate GitHub OAuth authorization URL."""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    callback_url = os.getenv("GITHUB_CALLBACK_URL")
    return f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={callback_url}&scope=repo,user"


def exchange_code_for_token(code: str):
    """Exchange authorization code for access token."""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    resp = requests.post("https://github.com/login/oauth/access_token", json={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code
    }, headers={"Accept": "application/json"})
    return resp.json()


def get_user_info(access_token: str):
    """Get GitHub user information using access token."""
    resp = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"})
    return resp.json()
