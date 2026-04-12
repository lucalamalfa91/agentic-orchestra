"""
Persistent encryption key management.
Stores ENCRYPTION_KEY in database/encryption.key (not in .env).
"""
from pathlib import Path
from cryptography.fernet import Fernet


# Path to persistent encryption key file (same folder as database)
KEY_FILE = Path(__file__).parent.parent.parent / "database" / "encryption.key"


def ensure_encryption_key() -> None:
    """
    Ensure encryption key exists in database/encryption.key.
    If missing, generates a new one and saves it.

    This runs on every app startup but only generates once.
    """
    # Ensure database directory exists
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if KEY_FILE.exists():
        # Key already exists, validate it
        try:
            key = KEY_FILE.read_text().strip()
            Fernet(key.encode())  # Test if valid
            print(f"[OK] Encryption key loaded from {KEY_FILE}")
            return
        except Exception as e:
            print(f"[WARNING] Invalid encryption key in {KEY_FILE}: {e}")
            print("  Generating new key (existing encrypted data will be invalid)")

    # Generate new key
    new_key = Fernet.generate_key().decode()
    KEY_FILE.write_text(new_key)

    # Set restrictive permissions (Unix only, ignored on Windows)
    try:
        KEY_FILE.chmod(0o600)  # rw------- (owner only)
    except Exception:
        pass  # Windows doesn't support chmod

    print(f"[OK] New encryption key generated and saved to {KEY_FILE}")
    print(f"  [WARNING] If you had existing API configurations, please reconfigure from UI Settings")


def get_encryption_key() -> bytes:
    """
    Get encryption key from persistent file.

    Returns:
        bytes: Encryption key for Fernet

    Raises:
        ValueError: If key file doesn't exist (should run ensure_encryption_key first)
    """
    if not KEY_FILE.exists():
        raise ValueError(
            f"Encryption key file not found: {KEY_FILE}\n"
            "Run ensure_encryption_key() on startup"
        )

    key = KEY_FILE.read_text().strip()
    return key.encode()
