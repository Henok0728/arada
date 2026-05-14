"""
ORM model package — re-exports all models so that:
  1. Alembic's `env.py` can import `Base.metadata` and see every table.
  2. Application code has a single import point:
       from app.db.models import Hotel, User, Referral, APIKey

Order matters: parent models (Hotel) before child models (User, Referral, APIKey)
to avoid import-time circular dependency issues.
"""
from app.db.base import Base  # noqa: F401 — needed for Base.metadata
from app.db.models.api_key import ENV_DEV, ENV_LIVE, VALID_SCOPES, APIKey  # noqa: F401
from app.db.models.hotel import Hotel, HotelCategory, HotelStatus  # noqa: F401
from app.db.models.referral import Referral, ReferralStatus, RoomType  # noqa: F401
from app.db.models.user import User, UserRole  # noqa: F401

__all__ = [
    "Base",
    # Hotel
    "Hotel",
    "HotelCategory",
    "HotelStatus",
    # User
    "User",
    "UserRole",
    # API Key
    "APIKey",
    "ENV_DEV",
    "ENV_LIVE",
    "VALID_SCOPES",
    # Referral
    "Referral",
    "ReferralStatus",
    "RoomType",
]
