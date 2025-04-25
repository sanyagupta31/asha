# src/security.py
import os
import hashlib
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Environment variables or fallback to simple default for demo
SECRET_KEY = os.getenv("ASHA_SECRET_KEY", "asha_demo_key_please_change_in_production")

def _get_encryption_key(salt: bytes = None):
    """Generate or derive encryption key from secret."""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key, salt

def encrypt_data(data: str) -> Dict[str, Any]:
    """
    Encrypt sensitive data for storage or transmission.
    
    Args:
        data: The string data to encrypt
    
    Returns:
        Dict with encrypted data and salt for decryption
    """
    key, salt = _get_encryption_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    
    return {
        "encrypted": base64.b64encode(encrypted_data).decode(),
        "salt": base64.b64encode(salt).decode()
    }

def decrypt_data(encrypted: str, salt: str) -> str:
    """
    Decrypt previously encrypted data.
    
    Args:
        encrypted: Base64-encoded encrypted data
        salt: Base64-encoded salt used during encryption
    
    Returns:
        Decrypted string
    """
    salt_bytes = base64.b64decode(salt)
    key, _ = _get_encryption_key(salt_bytes)
    
    f = Fernet(key)
    decrypted_data = f.decrypt(base64.b64decode(encrypted))
    
    return decrypted_data.decode()

def hash_session_id(session_id: str) -> str:
    """Create a secure hash of a session ID for lookups."""
    return hashlib.sha256(session_id.encode()).hexdigest()
