"""
Authentication and API Key service — Lodge-Link security foundation.

Responsibilities:
  1. Password hashing  — bcrypt via passlib (never SHA-256 for passwords)
  2. JWT generation    — short-lived access tokens + long-lived refresh tokens
  3. JWT verification  — decode, validate claims, return payload
  4. API key creation  — generate ll_dev_* / ll_live_* keys with 48 base62 chars
  5. API key hashing   — SHA-256(plaintext) for storage (NEVER store plaintext)
  6. API key lookup    — hash the incoming key, query the DB for the digest

Security invariants (enforced here, documented in CLAUDE.md):
  - Plaintext API keys are returned EXACTLY ONCE and never persisted.
  - SHA-256 hashing uses hashlib.sha256 — no salt needed (keys are high-entropy).
  - Passwords use bcrypt — salt is embedded in the hash by passlib automatically.
  - JWTs use HS256. The SECRET_KEY must be ≥ 32 random bytes in production.
  - Token type ("access" vs "refresh") is embedded in the JWT claim to prevent
    refresh tokens from being used as access tokens.

API Key format (CLAUDE.md §Key API Patterns):
  ll_{env}_{48 chars base62}
  Examples:
    ll_dev_aB3kR9xT2mP7qL0nE4wY6sD1cF8vH5jK2bN3gM9zU7oI
    ll_live_QwErTyUiOpAsdfGhJkLzXcVbNm1234567890AbCdEfGhIj
"""
import hashlib
import secrets
import string
<<<<<<< HEAD
from datetime import UTC, datetime, timedelta
from typing import Any
=======
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Base62 alphabet: [0-9A-Za-z] — URL-safe, no ambiguous chars, high entropy.
_BASE62_ALPHABET = string.ascii_letters + string.digits  # 62 chars
_API_KEY_SECRET_LENGTH = 48  # characters of the random suffix
_API_KEY_DISPLAY_PREFIX_LENGTH = 16  # how many chars to store for UI display

# JWT algorithm — HS256 is standard for single-service auth.
# Upgrade to RS256 in Phase 3 when we introduce a dedicated auth microservice.
JWT_ALGORITHM = "HS256"

# Token type claim values embedded in JWT payload
_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"

# ---------------------------------------------------------------------------
# Password hashing context (bcrypt)
# ---------------------------------------------------------------------------
# `deprecated="auto"` means passlib will auto-upgrade older hashes on verify.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===========================================================================
# Password utilities
# ===========================================================================

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt.

    The bcrypt hash includes the salt — no need to store it separately.
    The resulting string is safe to store directly in users.hashed_password.

    Args:
        plain_password: The user's plaintext password (e.g., from a form).

    Returns:
        A bcrypt hash string (60 chars, e.g. "$2b$12$...").
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Uses constant-time comparison internally — safe against timing attacks.

    Args:
        plain_password:  The candidate password to check.
        hashed_password: The stored bcrypt hash from users.hashed_password.

    Returns:
        True if the password matches; False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)


# ===========================================================================
# JWT utilities
# ===========================================================================

def _build_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
<<<<<<< HEAD
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Internal helper — encode a JWT with standard + custom claims."""
    now = datetime.now(UTC)
=======
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Internal helper — encode a JWT with standard + custom claims."""
    now = datetime.now(timezone.utc)
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1
    payload: dict[str, Any] = {
        "sub": subject,          # Subject (user UUID as string)
        "type": token_type,      # "access" or "refresh"
        "iat": now,              # Issued at
        "exp": now + expires_delta,  # Expiry
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(
    subject: str,
    *,
<<<<<<< HEAD
    hotel_id: str | None = None,
    role: str | None = None,
    expires_delta: timedelta | None = None,
=======
    hotel_id: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1
) -> str:
    """Create a short-lived JWT access token.

    Args:
        subject:       The user's UUID (str) — stored in the `sub` claim.
        hotel_id:      Hotel UUID (str) — embedded for downstream authorisation.
        role:          User role string (e.g., "ADMIN") — avoids DB round-trip.
        expires_delta: Custom TTL; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Signed JWT string ready to be returned in the auth response.
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    extra: dict[str, Any] = {}
    if hotel_id is not None:
        extra["hotel_id"] = hotel_id
    if role is not None:
        extra["role"] = role

    return _build_token(subject, _TOKEN_TYPE_ACCESS, delta, extra)


def create_refresh_token(
    subject: str,
    *,
<<<<<<< HEAD
    expires_delta: timedelta | None = None,
=======
    expires_delta: Optional[timedelta] = None,
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1
) -> str:
    """Create a long-lived JWT refresh token.

    Refresh tokens contain only `sub` and `type` — no role or hotel_id —
    so they cannot be used for resource authorisation directly.

    Args:
        subject:       The user's UUID (str).
        expires_delta: Custom TTL; defaults to REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
        Signed JWT refresh token string.
    """
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _build_token(subject, _TOKEN_TYPE_REFRESH, delta)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Validates:
      - Signature integrity (SECRET_KEY + HS256)
      - Token has not expired (`exp` claim)
      - Token type is "access" (prevents refresh token abuse)

    Args:
        token: Raw JWT string from the Authorization: Bearer header.

    Returns:
        Decoded payload dict (includes sub, hotel_id, role, exp, iat).

    Raises:
        ValueError: If the token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != _TOKEN_TYPE_ACCESS:
        raise ValueError("Token type mismatch: expected access token")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT refresh token.

    Validates signature, expiry, and that type == "refresh".

    Args:
        token: Raw JWT refresh token string.

    Returns:
        Decoded payload dict (includes sub, exp, iat).

    Raises:
        ValueError: If the token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"Invalid or expired refresh token: {exc}") from exc

    if payload.get("type") != _TOKEN_TYPE_REFRESH:
        raise ValueError("Token type mismatch: expected refresh token")

    return payload


# ===========================================================================
# API Key utilities
# ===========================================================================

def _generate_base62_secret(length: int = _API_KEY_SECRET_LENGTH) -> str:
    """Generate a cryptographically secure base62 string of `length` chars.

    Uses `secrets.choice` which draws from `os.urandom` — CSPRNG-backed.
    Entropy: 62^48 ≈ 2^285 — far beyond brute-force reach.
    """
    return "".join(secrets.choice(_BASE62_ALPHABET) for _ in range(length))


def generate_api_key(environment: str) -> tuple[str, str, str]:
    """Generate a new API key for a hotel.

    The plaintext key is returned to the caller ONCE and must be shown
    to the user immediately. It is NEVER stored anywhere in the system.
    Only the SHA-256 hash and display prefix are persisted.

    Key format:  ll_{env}_{48 base62 chars}
    Examples:
      ll_dev_aB3kR9xT2mP7qL0nE4wY6sD1cF8vH5jK2bN3gM9zU7oI
      ll_live_QwErTyUiOpAsdfGhJkLzXcVbNm1234567890AbCdEfGhIj

    Args:
        environment: "dev" or "live" — determines the key prefix.

    Returns:
        A tuple of (plaintext_key, key_hash, key_prefix):
          - plaintext_key: The full key string — show once, never store.
          - key_hash:      SHA-256 hex digest — store in api_keys.key_hash.
          - key_prefix:    First 16 chars of plaintext — store for UI display.

    Raises:
        ValueError: If environment is not "dev" or "live".
    """
<<<<<<< HEAD
    from app.db.models.api_key import ENV_DEV, ENV_LIVE, KEY_PREFIX_MAP
=======
    from app.db.models.api_key import KEY_PREFIX_MAP, ENV_DEV, ENV_LIVE
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1

    if environment not in (ENV_DEV, ENV_LIVE):
        raise ValueError(
            f"Invalid environment {environment!r}. Must be 'dev' or 'live'."
        )

    prefix = KEY_PREFIX_MAP[environment]          # "ll_dev_" or "ll_live_"
    secret = _generate_base62_secret()            # 48 base62 chars
    plaintext_key = f"{prefix}{secret}"           # full key

    key_hash = hash_api_key(plaintext_key)        # SHA-256 hex digest
    key_prefix = plaintext_key[:_API_KEY_DISPLAY_PREFIX_LENGTH]  # first 16 chars

    return plaintext_key, key_hash, key_prefix


def hash_api_key(plaintext_key: str) -> str:
    """Compute SHA-256 hex digest of a plaintext API key.

    This is the ONLY function that should be called to transform a key
    before storage or lookup. Using SHA-256 directly (no salt) is intentional:
    the key itself has ≈285 bits of entropy, making rainbow tables infeasible.

    Args:
        plaintext_key: The full API key string (e.g., "ll_dev_aB3k...").

    Returns:
        64-character lowercase hex string (SHA-256 digest).
    """
    return hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()


def verify_api_key_hash(plaintext_key: str, stored_hash: str) -> bool:
    """Constant-time comparison of a plaintext key's hash against a stored hash.

    Uses `secrets.compare_digest` to prevent timing attacks.

    Args:
        plaintext_key: The candidate key from the HTTP request header.
        stored_hash:   The SHA-256 hex digest from the api_keys table.

    Returns:
        True if the key matches the stored hash; False otherwise.
    """
    candidate_hash = hash_api_key(plaintext_key)
    return secrets.compare_digest(candidate_hash, stored_hash)


# ===========================================================================
# Token pair factory (convenience)
# ===========================================================================

def create_token_pair(
    user_id: str,
    hotel_id: str,
    role: str,
) -> dict[str, Any]:
    """Create both an access token and a refresh token for a login response.

    Args:
        user_id:  User UUID as string.
        hotel_id: Hotel UUID as string (embedded in access token only).
        role:     User role string (embedded in access token only).

    Returns:
        Dict with keys: access_token, refresh_token, token_type, expires_in.
    """
    access_token = create_access_token(
        subject=user_id, hotel_id=hotel_id, role=role
    )
    refresh_token = create_refresh_token(subject=user_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    }
