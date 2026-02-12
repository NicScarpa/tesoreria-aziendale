from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    if not settings.FERNET_KEY:
        raise ValueError("FERNET_KEY not configured. Generate with: Fernet.generate_key()")
    return Fernet(settings.FERNET_KEY.encode())


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext and return plaintext."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
