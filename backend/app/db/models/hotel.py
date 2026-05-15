"""
Hotel ORM model — lives in the `platform` schema (shared across all tenants).

Replaced PostGIS dependency with standard Float columns to ensure
compatibility with standard cloud database environments (like Railway).
"""
import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, Integer, String, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.referral import Referral
    from app.db.models.user import User
    from app.db.models.api_key import APIKey


class HotelCategory(str, enum.Enum):
    """Tier classification used for routing and trust-score weighting."""
    BUDGET = "BUDGET"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    LUXURY = "LUXURY"


class HotelStatus(str, enum.Enum):
    """KYC lifecycle state machine."""
    PENDING_KYC = "PENDING_KYC"
    SANDBOX = "SANDBOX"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Hotel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a lodging partner registered on the Lodge-Link platform."""

    __tablename__ = "hotels"
    __table_args__ = {"schema": "platform"}

    # ---- Identity -------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # ---- Geography ------------------------------------------------------
    country_code: Mapped[str] = mapped_column(
        String(2), nullable=False, default="ET", comment="ISO 3166-1 alpha-2"
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    # Standard Floats to avoid PostGIS dependency
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)

    # ---- Classification -------------------------------------------------
    category: Mapped[HotelCategory] = mapped_column(
        Enum(HotelCategory, schema="platform", name="hotel_category"),
        nullable=False,
        default=HotelCategory.STANDARD,
    )
    stars: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="1–5 star rating; null if unrated"
    )

    # ---- Status / KYC ---------------------------------------------------
    status: Mapped[HotelStatus] = mapped_column(
        Enum(HotelStatus, schema="platform", name="hotel_status"),
        nullable=False,
        default=HotelStatus.PENDING_KYC,
        index=True,
    )
    kyc_approved_at: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )

    # ---- Contact --------------------------------------------------------
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ---- Referral config ------------------------------------------------
    is_referral_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
    )

    # ---- Relationships --------------------------------------------------
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="hotel", cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="hotel", cascade="all, delete-orphan"
    )
    outbound_referrals: Mapped[List["Referral"]] = relationship(
        "Referral",
        foreign_keys="[Referral.origin_hotel_id]",
        back_populates="origin_hotel",
    )
    inbound_referrals: Mapped[List["Referral"]] = relationship(
        "Referral",
        foreign_keys="[Referral.destination_hotel_id]",
        back_populates="destination_hotel",
    )

    def __repr__(self) -> str:
        return f"<Hotel id={self.id} slug={self.slug!r} status={self.status}>"
