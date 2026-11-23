import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
import jwt

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

from app.core.config import settings


def hash_password(password: str) -> str:
    """
    High security password hashing.
    Uses bcrypt with 12 rounds or standard library scrypt with salt.
    """
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        # Secure fallback using Python's built-in scrypt
        salt = secrets.token_hex(16)
        key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            n=16384,
            r=8,
            p=1,
            maxmem=0,
            dklen=64,
        )
        return f"scrypt${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Constant-time password verification to prevent timing attacks.
    """
    if not hashed_password or not plain_password:
        return False

    try:
        # Check standard bcrypt formats ($2a$, $2b$, $2y$)
        if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            if not HAS_BCRYPT:
                return False
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

        # Check scrypt fallback format
        if hashed_password.startswith("scrypt$"):
            parts = hashed_password.split("$")
            if len(parts) != 3:
                return False
            salt = parts[1]
            stored_key_hex = parts[2]
            computed_key = hashlib.scrypt(
                plain_password.encode("utf-8"),
                salt=salt.encode("utf-8"),
                n=16384,
                r=8,
                p=1,
                maxmem=0,
                dklen=64,
            )
            return secrets.compare_digest(computed_key.hex(), stored_key_hex)

        # Legacy prefixed bcrypt support
        if hashed_password.startswith("bcrypt$"):
            raw_hash = hashed_password[7:]
            if HAS_BCRYPT:
                return bcrypt.checkpw(plain_password.encode("utf-8"), raw_hash.encode("utf-8"))

        return False
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str,
    username: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generates a cryptographically signed JWT token with expiry and anti-tamper claims.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "username": username or str(subject),
        "iat": now,
        "nbf": now,
        "exp": expire,
        "jti": secrets.token_hex(16),
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and strictly validates a JWT token.
    Enforces algorithm matching to prevent algorithm substitution attacks.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "iat"]},
        )
        return payload
    except jwt.PyJWTError:
        return None
