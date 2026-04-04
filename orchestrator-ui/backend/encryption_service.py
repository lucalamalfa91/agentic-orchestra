"""
Encryption service for sensitive data like API keys.
"""
from cryptography.fernet import Fernet
import os


def get_encryption_key():
    """Get encryption key from environment variable."""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set")
    return key.encode()


def encrypt(plaintext: str) -> str:
    """
    Encrypt plaintext string.

    Args:
        plaintext: String to encrypt

    Returns:
        Encrypted string (base64 encoded)
    """
    f = Fernet(get_encryption_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """
    Decrypt ciphertext string.

    Args:
        ciphertext: Encrypted string (base64 encoded)

    Returns:
        Decrypted plaintext string
    """
    f = Fernet(get_encryption_key())
    return f.decrypt(ciphertext.encode()).decode()
