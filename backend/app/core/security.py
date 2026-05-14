import hashlib
import hmac
import uuid

def generate_handshake_code(referral_id: uuid.UUID, hotel_id: uuid.UUID, secret_key: str) -> str:
    """
    Generate a 6-digit cryptographically secure handshake code using HMAC-SHA256.
    """
    message = f"{referral_id}:{hotel_id}".encode("utf-8")
    key = secret_key.encode("utf-8")
    
    # Generate HMAC
    hmac_hash = hmac.new(key, message, hashlib.sha256).digest()
    
    # Truncate to get a 6-digit code (similar to HOTP/TOTP truncation)
    offset = hmac_hash[-1] & 0x0F
    truncated_hash = (
        (hmac_hash[offset] & 0x7F) << 24 |
        (hmac_hash[offset + 1] & 0xFF) << 16 |
        (hmac_hash[offset + 2] & 0xFF) << 8 |
        (hmac_hash[offset + 3] & 0xFF)
    )
    
    # Get 6 digits
    code = str(truncated_hash % 1000000).zfill(6)
    return code

def hash_handshake_code(code: str) -> str:
    """
    Hash the 6-digit code for secure storage in DB or Redis.
    """
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
