"""
set_ai_config.py  —  seed or update the `configurations` table.

Usage (run from the repo root or from orchestrator-ui/backend/):

    python orchestrator-ui/backend/set_ai_config.py \\
        --url  https://adesso-ai-hub.3asabc.de/v1 \\
        --key  sk-YOUR_REAL_KEY_HERE

Optional flags:
    --user-id   <int>   target a specific user row (default: first user found)
    --list              print current configurations and exit (key masked)

The script:
  1. Loads .env from the repo root (for DATABASE_URL and ENCRYPTION_KEY).
  2. Encrypts the key with the same Fernet cipher used at runtime.
  3. Deactivates any existing configuration for the user.
  4. Inserts a new active configuration row.
"""
import argparse
import sys
from pathlib import Path

# ── path setup so imports work whether called from root or from backend/ ───────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")          # load DATABASE_URL + ENCRYPTION_KEY
load_dotenv(BACKEND_DIR / ".env")        # fallback: backend-local .env

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Configuration
from encryption_service import encrypt, decrypt


# ── helpers ───────────────────────────────────────────────────────────────────

def _mask(key: str) -> str:
    if not key or len(key) < 10:
        return repr(key)
    return f"{key[:6]}...{key[-4:]}  (len={len(key)})"


def _list_configs(db: Session):
    rows = db.query(Configuration).all()
    if not rows:
        print("configurations table is empty.")
        return
    print(f"{'id':>4}  {'user_id':>7}  {'active':>6}  {'url':<45}  key")
    print("-" * 90)
    for c in rows:
        try:
            plain = decrypt(c.ai_api_key_encrypted)
        except Exception:
            plain = "<decrypt error>"
        print(f"{c.id:>4}  {c.user_id:>7}  {str(c.is_active):>6}  {c.ai_base_url:<45}  {_mask(plain)}")


def _get_or_create_mock_user(db: Session, user_id: int | None) -> User:
    """Return existing user or create a minimal placeholder for local dev."""
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"[ERROR] No user with id={user_id} found.")
            sys.exit(1)
        return user

    user = db.query(User).first()
    if user:
        print(f"[INFO] Using existing user: id={user.id}  github_username={user.github_username}")
        return user

    # No users at all — create a local dev placeholder
    print("[INFO] No users found — creating a local-dev placeholder user (id will be 1).")
    placeholder = User(
        github_id="local-dev-0",
        github_username="local-dev",
        github_token="placeholder",
    )
    db.add(placeholder)
    db.commit()
    db.refresh(placeholder)
    print(f"[OK]   Placeholder user created: id={placeholder.id}")
    return placeholder


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Seed or update the configurations table with AI provider credentials."
    )
    parser.add_argument("--url",     help="AI base URL  e.g. https://adesso-ai-hub.3asabc.de/v1")
    parser.add_argument("--key",     help="Plain-text API key (will be encrypted before storage)")
    parser.add_argument("--user-id", type=int, default=None,
                        help="Target user id (default: first user in DB)")
    parser.add_argument("--list",    action="store_true",
                        help="List existing configurations and exit")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        if args.list:
            _list_configs(db)
            return

        if not args.url or not args.key:
            parser.error("--url and --key are required (unless --list is used)")

        user = _get_or_create_mock_user(db, args.user_id)

        # Deactivate all previous configs for this user
        deactivated = (
            db.query(Configuration)
            .filter(Configuration.user_id == user.id)
            .update({"is_active": False})
        )
        if deactivated:
            print(f"[INFO] Deactivated {deactivated} previous configuration(s) for user {user.id}.")

        # Encrypt and insert new config
        encrypted_key = encrypt(args.key)
        config = Configuration(
            user_id=user.id,
            ai_base_url=args.url,
            ai_api_key_encrypted=encrypted_key,
            is_active=True,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        print(f"[OK]   Configuration saved:")
        print(f"       id          = {config.id}")
        print(f"       user_id     = {config.user_id}")
        print(f"       ai_base_url = {config.ai_base_url}")
        print(f"       key (plain) = {_mask(args.key)}")
        print(f"       is_active   = {config.is_active}")
        print()
        print("Run the generation again — the orchestrator will pick up this config automatically.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
