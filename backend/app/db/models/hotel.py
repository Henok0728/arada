"""
Hotel ORM model — lives in the `platform` schema (shared across all tenants).

PostGIS column: `location` is stored as GEOGRAPHY(POINT, 4326) so that
PostGIS distance / radius functions (ST_DWithin, ST_Distance) work correctly
with metre-based inputs on a WGS-84 spheroid — no planar projection needed.

Category and Status use native PostgreSQL enums for DB-level constraint enforcement.
"""
from enum import StrEnum
from typing import TYPE_CHECKING

from geoalchemy2 import Geography  # type: ignore[import]
from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.api_key import APIKey
    from app.db.models.referral import Referral
    from app.db.models.user import User


class HotelCategory(StrEnum):
    """Tier classification used for routing and trust-score weighting."""
    BUDGET = "BUDGET"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    LUXURY = "LUXURY"


class HotelStatus(StrEnum):
    """KYC lifecycle state machine.

    PENDING_KYC  → SANDBOX (after document upload)
    SANDBOX      → ACTIVE  (after KYC approval by Lodge-Link ops)
    ACTIVE       → SUSPENDED (manual by ops for policy violations)
    SUSPENDED    → ACTIVE (after remediation)
    """
    PENDING_KYC = "PENDING_KYC"
    SANDBOX = "SANDBOX"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Hotel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a lodging partner registered on the Lodge-Link platform.

    Schema: `platform` — shared across all tenants.
    Each hotel also gets a private schema `hotel_{slug}` (created separately).
    """

    __tablename__ = "hotels"
    __table_args__ = {"schema": "platform"}

    # ---- Identity -------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # ---- Geography ------------------------------------------------------
    # Multi-country ready: never hardcode "ET" — read from hotel record.
    country_code: Mapped[str] = mapped_column(
        String(2), nullable=False, default="ET", comment="ISO 3166-1 alpha-2"
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    # PostGIS GEOGRAPHY(POINT, 4326): lat/lng stored as geographic coordinates.
    # Use ST_DWithin(location, ST_MakePoint(lng, lat)::geography, radius_metres)
    # for geo-radius queries. Returns True/False without a full table scan
    # when a GIST index is present (added in migration).
    location: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        comment="PostGIS GEOGRAPHY(POINT, 4326) — WGS-84 lng/lat",
    )

    # ---- Classification -------------------------------------------------
    category: Mapped[HotelCategory] = mapped_column(
        Enum(HotelCategory, schema="platform", name="hotel_category"),
        nullable=False,
        default=HotelCategory.STANDARD,
    )
    stars: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="1–5 star rating; null if unrated"
    )

    # ---- Status / KYC ---------------------------------------------------
    status: Mapped[HotelStatus] = mapped_column(
        Enum(HotelStatus, schema="platform", name="hotel_status"),
        nullable=False,
        default=HotelStatus.PENDING_KYC,
        index=True,
    )
    kyc_approved_at: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # datetime stored as ISO string for cross-TZ safety; cast in service layer

    # ---- Contact --------------------------------------------------------
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ---- Referral config ------------------------------------------------
    is_referral_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Whether this hotel participates in the referral network"
    )

    # ---- Relationships --------------------------------------------------
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="hotel", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey", back_populates="hotel", cascade="all, delete-orphan"
    )
    outbound_referrals: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="[Referral.origin_hotel_id]",
        back_populates="origin_hotel",
    )
    inbound_referrals: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="[Referral.destination_hotel_id]",
        back_populates="destination_hotel",
    )

    def __repr__(self) -> str:
        return f"<Hotel id={self.id} slug={self.slug!r} status={self.status}>"
