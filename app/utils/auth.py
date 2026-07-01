import hashlib
import os

def generate_salt():
    return os.urandom(16).hex()

def hash_password(password: str, salt: str = None) -> str:
    """
    Hashes a password using PBKDF2 with SHA-256.
    Returns format: pbkdf2:sha256:iterations$salt$hash
    """
    iterations = 260000
    if not salt:
        salt = generate_salt()
    # Ensure salt and password are bytes
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    dk = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${dk.hex()}"

def check_password(password: str, hashed_password: str) -> bool:
    """
    Checks if a password matches the PBKDF2 hash.
    """
    try:
        if not hashed_password.startswith("pbkdf2:sha256:"):
            return False
        parts = hashed_password.split('$')
        if len(parts) != 3:
            return False
        iterations_part, salt, hash_hex = parts
        iterations = int(iterations_part.split(':')[-1])
        
        pwd_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        dk = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
        return dk.hex() == hash_hex
    except Exception:
        return False

def hash_fingerprint_file(file_bytes: bytes) -> str:
    """
    Generates a SHA-256 hex digest of file bytes for fingerprint proxy verification.
    """
    return hashlib.sha256(file_bytes).hexdigest()
