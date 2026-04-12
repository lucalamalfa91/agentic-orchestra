"""
Encryption service for sensitive data like API keys.
Uses persistent key from database/encryption.key instead of .env.
"""
from cryptography.fernet import Fernet
from encryption_init import get_encryption_key as _get_key


def get_encryption_key():
    """
    Get encryption key from persistent file.
    Uses encryption_init.get_encryption_key() which reads from database/encryption.key.
    """
    return _get_key()


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
