"""
Persistent encryption key management.
Reads ENCRYPTION_KEY env var first (required on stateless cloud deployments).
Falls back to database/encryption.key for local development.
"""
import os
from pathlib import Path
from cryptography.fernet import Fernet


KEY_FILE = Path(__file__).parent.parent.parent / "database" / "encryption.key"


def ensure_encryption_key() -> None:
    """
    Ensure a valid encryption key is available.
    On cloud deployments, set the ENCRYPTION_KEY environment variable.
    Locally, the key is auto-generated and saved to database/encryption.key.
    """
    env_key = os.getenv("ENCRYPTION_KEY")
    if env_key:
        try:
            Fernet(env_key.encode())
            print("[OK] Encryption key loaded from ENCRYPTION_KEY env var")
            return
        except Exception as e:
            raise ValueError(f"ENCRYPTION_KEY env var is set but invalid: {e}")

    # Local dev: use persistent file
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if KEY_FILE.exists():
        try:
            key = KEY_FILE.read_text().strip()
            Fernet(key.encode())
            print(f"[OK] Encryption key loaded from {KEY_FILE}")
            return
        except Exception as e:
            print(f"[WARNING] Invalid encryption key in {KEY_FILE}: {e}")
            print("  Generating new key (existing encrypted data will be invalid)")

    new_key = Fernet.generate_key().decode()
    KEY_FILE.write_text(new_key)
    try:
        KEY_FILE.chmod(0o600)
    except Exception:
        pass

    print(f"[OK] New encryption key generated and saved to {KEY_FILE}")
    print("  [WARNING] If you had existing API configurations, please reconfigure from UI Settings")


def get_encryption_key() -> bytes:
    """
    Return the active encryption key as bytes.
    Reads from ENCRYPTION_KEY env var first, then from the local key file.
    """
    env_key = os.getenv("ENCRYPTION_KEY")
    if env_key:
        return env_key.encode()

    if not KEY_FILE.exists():
        raise ValueError(
            f"Encryption key file not found: {KEY_FILE}\n"
            "Run ensure_encryption_key() on startup or set the ENCRYPTION_KEY env var."
        )

    return KEY_FILE.read_text().strip().encode()
