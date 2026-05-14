"""
Unit tests for app/services/auth.py

These tests are pure Python — no database, no HTTP, no I/O.
They validate every public function in the auth service:
  - password hashing + verification
  - access token creation + decoding
  - refresh token creation + decoding
  - token type enforcement (refresh token cannot be used as access)
  - expired token rejection
  - API key generation format validation
  - API key SHA-256 hashing
  - API key constant-time verification
  - token pair factory output shape
"""
<<<<<<< HEAD
=======
import time
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1
from datetime import timedelta

import pytest

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_access_token,
    decode_refresh_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_api_key_hash,
    verify_password,
)


# ===========================================================================
# Password hashing
# ===========================================================================
class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        result = hash_password("MySecretPass!")
        assert isinstance(result, str)

    def test_hash_password_starts_with_bcrypt_prefix(self):
        result = hash_password("MySecretPass!")
        assert result.startswith("$2b$")

    def test_hash_password_is_not_plaintext(self):
        plain = "MySecretPass!"
        assert hash_password(plain) != plain

    def test_hash_password_different_hashes_per_call(self):
        """bcrypt embeds a random salt — same password ≠ same hash."""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2

    def test_verify_password_correct(self):
        plain = "CorrectHorseBatteryStaple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_wrong(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_empty_string(self):
        hashed = hash_password("some_password")
        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False


# ===========================================================================
# JWT — Access tokens
# ===========================================================================
class TestAccessToken:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-uuid-123")
        assert isinstance(token, str)
        # JWTs have exactly 3 dot-separated parts
        assert len(token.split(".")) == 3

    def test_decode_access_token_sub_claim(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        payload = decode_access_token(token)
        assert payload["sub"] == user_id

    def test_decode_access_token_type_claim(self):
        token = create_access_token("user-uuid-123")
        payload = decode_access_token(token)
        assert payload["type"] == "access"

    def test_decode_access_token_hotel_id_claim(self):
        hotel_id = "hotel-uuid-456"
        token = create_access_token("user-uuid-123", hotel_id=hotel_id)
        payload = decode_access_token(token)
        assert payload["hotel_id"] == hotel_id

    def test_decode_access_token_role_claim(self):
        token = create_access_token("user-uuid-123", role="ADMIN")
        payload = decode_access_token(token)
        assert payload["role"] == "ADMIN"

    def test_decode_access_token_has_exp_and_iat(self):
        token = create_access_token("user-uuid-123")
        payload = decode_access_token(token)
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_access_token_raises(self):
        token = create_access_token(
            "user-uuid-123",
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_access_token(token)

    def test_tampered_token_raises(self):
        token = create_access_token("user-uuid-123")
        # Flip a character in the signature (last segment)
        parts = token.split(".")
        parts[2] = parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
        bad_token = ".".join(parts)
        with pytest.raises(ValueError):
            decode_access_token(bad_token)

    def test_random_string_raises(self):
        with pytest.raises(ValueError):
            decode_access_token("not.a.jwt")


# ===========================================================================
# JWT — Refresh tokens
# ===========================================================================
class TestRefreshToken:
    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token("user-uuid-123")
        assert isinstance(token, str)

    def test_decode_refresh_token_sub_claim(self):
        user_id = "refresh-user-uuid"
        token = create_refresh_token(user_id)
        payload = decode_refresh_token(token)
        assert payload["sub"] == user_id

    def test_decode_refresh_token_type_claim(self):
        token = create_refresh_token("user-uuid-123")
        payload = decode_refresh_token(token)
        assert payload["type"] == "refresh"

    def test_expired_refresh_token_raises(self):
        token = create_refresh_token(
            "user-uuid-123",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            decode_refresh_token(token)


# ===========================================================================
# JWT — Token type enforcement (cross-token abuse prevention)
# ===========================================================================
class TestTokenTypeEnforcement:
    def test_refresh_token_rejected_as_access_token(self):
        """A refresh token MUST NOT pass access token validation."""
        refresh = create_refresh_token("user-uuid-123")
        with pytest.raises(ValueError, match="Token type mismatch"):
            decode_access_token(refresh)

    def test_access_token_rejected_as_refresh_token(self):
        """An access token MUST NOT pass refresh token validation."""
        access = create_access_token("user-uuid-123")
        with pytest.raises(ValueError, match="Token type mismatch"):
            decode_refresh_token(access)


# ===========================================================================
# API Key generation
# ===========================================================================
class TestAPIKeyGeneration:
    def test_generate_dev_key_format(self):
        plaintext, key_hash, key_prefix = generate_api_key("dev")
        assert plaintext.startswith("ll_dev_"), (
            f"Expected ll_dev_ prefix, got: {plaintext[:10]}"
        )

    def test_generate_live_key_format(self):
        plaintext, key_hash, key_prefix = generate_api_key("live")
        assert plaintext.startswith("ll_live_"), (
            f"Expected ll_live_ prefix, got: {plaintext[:12]}"
        )

    def test_generate_dev_key_total_length(self):
        plaintext, _, _ = generate_api_key("dev")
        # "ll_dev_" (7) + 48 base62 chars = 55 chars
        assert len(plaintext) == 55, f"Got length {len(plaintext)}"

    def test_generate_live_key_total_length(self):
        plaintext, _, _ = generate_api_key("live")
        # "ll_live_" (8) + 48 base62 chars = 56 chars
        assert len(plaintext) == 56, f"Got length {len(plaintext)}"

    def test_key_secret_uses_base62_alphabet(self):
        import string
        alphabet = set(string.ascii_letters + string.digits)
        plaintext, _, _ = generate_api_key("dev")
        # The suffix after "ll_dev_" must be base62
        suffix = plaintext[len("ll_dev_"):]
        assert all(c in alphabet for c in suffix), (
            f"Non-base62 char found in: {suffix}"
        )

    def test_hash_is_64_char_hex(self):
        _, key_hash, _ = generate_api_key("dev")
        assert len(key_hash) == 64
        assert all(c in "0123456789abcdef" for c in key_hash)

    def test_key_prefix_is_16_chars(self):
        plaintext, _, key_prefix = generate_api_key("dev")
        assert len(key_prefix) == 16
        assert plaintext.startswith(key_prefix)

    def test_two_keys_are_unique(self):
        """Each generated key must be unique (probability of collision ≈ 0)."""
        key1, _, _ = generate_api_key("dev")
        key2, _, _ = generate_api_key("dev")
        assert key1 != key2

    def test_invalid_environment_raises(self):
        with pytest.raises(ValueError, match="Invalid environment"):
            generate_api_key("staging")

    def test_invalid_environment_prod_raises(self):
        with pytest.raises(ValueError, match="Invalid environment"):
            generate_api_key("prod")


# ===========================================================================
# API Key hashing + verification
# ===========================================================================
class TestAPIKeyHashing:
    def test_hash_is_deterministic(self):
        """Same plaintext key → same SHA-256 hash, always."""
        key = "ll_dev_aB3kR9xT2mP7qL0nE4wY6sD1cF8vH5jK2bN3gM9zU7oI"
        assert hash_api_key(key) == hash_api_key(key)

    def test_different_keys_produce_different_hashes(self):
        key1 = "ll_dev_aB3kR9xT2mP7qL0nE4wY6sD1cF8vH5jK2bN3gM9zU7oI"
        key2 = "ll_dev_bC4lS0yU3nQ8rM1oF5xZ7tE2dG9wI6kL3cO4hN0aV8pJ"
        assert hash_api_key(key1) != hash_api_key(key2)

    def test_verify_correct_key(self):
        plaintext, stored_hash, _ = generate_api_key("dev")
        assert verify_api_key_hash(plaintext, stored_hash) is True

    def test_verify_wrong_key(self):
        _, stored_hash, _ = generate_api_key("dev")
        wrong_key, _, _ = generate_api_key("dev")
        assert verify_api_key_hash(wrong_key, stored_hash) is False

    def test_verify_empty_key_fails(self):
        _, stored_hash, _ = generate_api_key("dev")
        assert verify_api_key_hash("", stored_hash) is False

    def test_verify_live_key_against_dev_hash_fails(self):
        dev_plain, dev_hash, _ = generate_api_key("dev")
        live_plain, _, _ = generate_api_key("live")
        assert verify_api_key_hash(live_plain, dev_hash) is False


# ===========================================================================
# Token pair factory
# ===========================================================================
class TestCreateTokenPair:
    def test_token_pair_keys(self):
        result = create_token_pair(
            user_id="user-uuid",
            hotel_id="hotel-uuid",
            role="ADMIN",
        )
        assert set(result.keys()) == {
            "access_token", "refresh_token", "token_type", "expires_in"
        }

    def test_token_pair_token_type_is_bearer(self):
        result = create_token_pair("u", "h", "RECEPTIONIST")
        assert result["token_type"] == "bearer"

    def test_token_pair_expires_in_is_seconds(self):
        from app.core.config import settings
        result = create_token_pair("u", "h", "VIEWER")
        assert result["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_token_pair_access_token_is_valid(self):
        result = create_token_pair("user-uuid-789", "hotel-uuid-789", "ADMIN")
        payload = decode_access_token(result["access_token"])
        assert payload["sub"] == "user-uuid-789"
        assert payload["hotel_id"] == "hotel-uuid-789"
        assert payload["role"] == "ADMIN"

    def test_token_pair_refresh_token_is_valid(self):
        result = create_token_pair("user-uuid-789", "hotel-uuid-789", "ADMIN")
        payload = decode_refresh_token(result["refresh_token"])
        assert payload["sub"] == "user-uuid-789"
        # Refresh token must NOT contain hotel_id or role
        assert "hotel_id" not in payload
        assert "role" not in payload
