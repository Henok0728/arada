"""
Auth & Registration Pydantic schemas.

Separation of concerns:
  - HotelRegisterRequest  — one payload creates both a Hotel + a User (ADMIN)
  - TokenRequest          — standard OAuth2-style username/password form
  - TokenResponse         — returns both access + refresh tokens
  - RegisterResponse      — returns token pair + the plaintext API key (shown ONCE)
"""
import uuid
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.db.models.api_key import VALID_SCOPES


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class HotelRegisterRequest(BaseModel):
    """Single payload to create a Hotel tenant + its first ADMIN user."""

    # Hotel details
    hotel_name: str = Field(min_length=2, max_length=255)
    hotel_slug: str = Field(
        min_length=2, max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="URL-safe slug, e.g. 'blue-nile-lodge'",
    )
    city: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=5, max_length=500)
    phone_number: str = Field(
        pattern=r"^\+\d{7,15}$",
        description="E.164 format, e.g. +251911234567",
    )
    country_code: str = Field(default="ET", min_length=2, max_length=2)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    # Admin user
    admin_email: EmailStr
    admin_full_name: str = Field(min_length=2, max_length=255)
    admin_password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    hotel: dict
    sandbox_key: str
    kyc_status: str
    next_steps: List[str]
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TokenRequest(BaseModel):
    """Standard email/password login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned on successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    hotel_id: uuid.UUID
    display_name: str
    kyc_status: str
    is_platform_admin: bool
    plan_name: str
