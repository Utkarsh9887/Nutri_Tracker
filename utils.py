# utils.py
import os
import hashlib
import binascii
from datetime import datetime

from constant import PWD_HASH_ITERATIONS, PWD_HASH_NAME, PWD_SALT_BYTES

def generate_salt():
    return os.urandom(PWD_SALT_BYTES)

def hash_password(password: str, salt: bytes):
    """
    Return hex-encoded hash for storage and hex-encoded salt.
    Uses PBKDF2-HMAC with SHA-256.
    """
    if isinstance(password, str):
        password = password.encode("utf-8")
    dk = hashlib.pbkdf2_hmac(PWD_HASH_NAME, password, salt, PWD_HASH_ITERATIONS)
    return binascii.hexlify(dk).decode(), binascii.hexlify(salt).decode()

def verify_password(password: str, stored_hash_hex: str, stored_salt_hex: str) -> bool:
    salt = binascii.unhexlify(stored_salt_hex.encode())
    h, _ = hash_password(password, salt)
    return h == stored_hash_hex

def parse_date(date_str: str):
    """
    Parse YYYY-MM-DD. If invalid, raise ValueError.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        raise ValueError("Date must be YYYY-MM-DD") from e

def is_number(s):
    try:
        float(s)
        return True
    except:
        return False

def warn(msg):
    # simple logger replacement (you can swap for logging module)
    print(f"[WARN] {msg}")

def info(msg):
    print(f"[INFO] {msg}")
