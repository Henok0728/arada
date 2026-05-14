"""
User ORM model — platform.users table.

Passwords are NEVER stored in plaintext. The `hashed_password` column stores
a bcrypt hash produced by passlib. Auth logic is in `app/services/auth.py`.

Role hierarchy:
  ADMIN        — full hotel dashboard access (can generate API keys)
  RECEPTIONIST — can initiate referrals and view room availability
  VIEWER       — read-only analytics access
"""
import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.hotel import Hotel


class UserRole(StrEnum):
    """Role enum for RBAC within a hotel account."""
    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    VIEWER = "VIEWER"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user account tied to a specific hotel tenant.

    Schema: `platform` — shared table; hotel isolation is enforced via
    the `hotel_id` FK and Row Level Security on the private hotel schemas.
    """

    __tablename__ = "users"
    __table_args__ = {"schema": "platform"}

    # ---- Hotel tenancy --------------------------------------------------
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform.hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---- Identity -------------------------------------------------------
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ---- Auth -----------------------------------------------------------
    # bcrypt hash via passlib — never the plaintext password.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ---- RBAC -----------------------------------------------------------
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, schema="platform", name="user_role"),
        nullable=False,
        default=UserRole.RECEPTIONIST,
    )

    # ---- Account state --------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Email verification flag"
    )
    last_login_at: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    # ---- Relationships --------------------------------------------------
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
