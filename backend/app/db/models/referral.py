"""
Referral ORM model — platform.referrals table.

State machine (enforced in the service layer, reflected here via timestamps):

  PENDING   ──► ACCEPTED  (destination hotel accepts via POST .../accept)
            ──► DECLINED  (destination hotel declines via POST .../decline)
            ──► EXPIRED   (Celery task marks after TTL with no response)

  ACCEPTED  ──► COMPLETED (HMAC handshake code validated at check-in)
            ──► CANCELLED (guest no-show or cancellation)

  DECLINED, EXPIRED, COMPLETED, CANCELLED are terminal states.

The fanout loop (asyncio.gather) creates one Referral row per candidate hotel
with status=PENDING. Only the first hotel to ACCEPT wins; the others
are automatically DECLINED by the fanout service.
"""
import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.hotel import Hotel


class ReferralStatus(StrEnum):
    """All possible states a referral can be in.

    String values are stored verbatim in PostgreSQL for readability in
    direct DB queries and log analysis.
    """
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class RoomType(StrEnum):
    """Common room type taxonomy used across the referral network."""
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TWIN = "TWIN"
    SUITE = "SUITE"
    FAMILY = "FAMILY"
    DORMITORY = "DORMITORY"


class Referral(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single referral event from one hotel to another.

    Schema: `platform.referrals` — referenced in the Phase 1 exit criterion:
    "50+ real referral events logged in platform.referral_events" (table name
    is `referrals`; the exit criterion uses the colloquial term).

    Each row tracks one guest referral attempt. Multiple rows may share the
    same `session_id` (one fanout attempt = many parallel Referral rows).
    """

    __tablename__ = "referrals"
    __table_args__ = {"schema": "platform"}

    # ---- Fanout session grouping ----------------------------------------
    # A single receptionist action fans out to N hotels; all share a session_id.
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        default=uuid.uuid4,
        comment="Groups all Referral rows created in one fanout call",
    )

    # ---- Hotels (parties) -----------------------------------------------
    origin_hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform.hotels.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="Hotel that initiated the referral (Hotel A)",
    )
    # Nullable: set at PENDING creation; confirmed when a specific destination
    # hotel accepts. In fanout mode, each row targets one candidate.
    destination_hotel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform.hotels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Hotel that was referred to (Hotel B); null before acceptance",
    )

    # ---- Guest details --------------------------------------------------
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guest_phone: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="Formatted E.164 phone number, e.g. +251911234567"
    )

    # ---- Stay details ---------------------------------------------------
    room_type: Mapped[RoomType] = mapped_column(
        Enum(RoomType, schema="platform", name="room_type"),
        nullable=False,
        default=RoomType.DOUBLE,
    )
    check_in_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="ISO date YYYY-MM-DD"
    )
    check_out_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="ISO date YYYY-MM-DD"
    )
    party_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    special_requests: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # ---- State machine --------------------------------------------------
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, schema="platform", name="referral_status"),
        nullable=False,
        default=ReferralStatus.PENDING,
        index=True,
    )

    # ---- HMAC handshake code (set on ACCEPTED, validated on COMPLETED) ---
    # The HMAC code is generated server-side (Module 6 §6.2) and sent via SMS.
    # Stored here so the offline validator can verify without an API call.
    handshake_code: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True,
        comment="HMAC-SHA256 offline validation code — see handshake service"
    )
    handshake_validated_at: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="ISO datetime when code was validated at check-in"
    )

    # ---- Lifecycle timestamps -------------------------------------------
    accepted_at: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="ISO datetime when destination hotel accepted"
    )
    declined_at: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    completed_at: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="ISO datetime of successful check-in (COMPLETED)"
    )
    expired_at: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="ISO datetime when Celery marked referral expired"
    )
    cancelled_at: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    # ---- Internal notes -------------------------------------------------
    decline_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---- Relationships --------------------------------------------------
    origin_hotel: Mapped["Hotel"] = relationship(
        "Hotel",
        foreign_keys=[origin_hotel_id],
        back_populates="outbound_referrals",
    )
    destination_hotel: Mapped[Optional["Hotel"]] = relationship(
        "Hotel",
        foreign_keys=[destination_hotel_id],
        back_populates="inbound_referrals",
    )

    def is_terminal(self) -> bool:
        """Returns True if this referral is in a terminal (non-transitionable) state."""
        return self.status in {
            ReferralStatus.COMPLETED,
            ReferralStatus.DECLINED,
            ReferralStatus.EXPIRED,
            ReferralStatus.CANCELLED,
        }

    def __repr__(self) -> str:
        return (
            f"<Referral id={self.id} session={self.session_id} "
            f"status={self.status} guest={self.guest_name!r}>"
        )
