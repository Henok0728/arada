"""
Referral Pydantic schemas — request validation and response serialisation.

The FanoutRequest drives the core referral broadcast.
The FanoutResponse returns the session_id so the receptionist
can poll for accepted status.
"""
import uuid
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.db.models.referral import ReferralStatus, RoomType


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class FanoutRequest(BaseModel):
    """Payload from the receptionist initiating a referral fan-out."""

    origin_hotel_id: uuid.UUID = Field(
        description="UUID of the hotel initiating the referral (Hotel A)"
    )
    guest_name: str = Field(min_length=1, max_length=255)
    guest_phone: str = Field(
        description="E.164 phone number e.g. +251911234567",
        pattern=r"^\+\d{7,15}$",
    )
    room_type: RoomType = RoomType.DOUBLE
    party_size: int = Field(default=1, ge=1, le=20)
    check_in_date: Optional[str] = Field(
        default=None, description="ISO date YYYY-MM-DD"
    )
    check_out_date: Optional[str] = Field(
        default=None, description="ISO date YYYY-MM-DD"
    )
    special_requests: Optional[str] = Field(default=None, max_length=1000)

    # Geo-context: where is Hotel A right now?
    origin_longitude: float = Field(ge=-180.0, le=180.0)
    origin_latitude: float = Field(ge=-90.0, le=90.0)
    radius_metres: float = Field(
        default=5000.0, ge=100.0, le=50000.0,
        description="Search radius for candidate hotels (default 5 km)"
    )

    # Idempotency key provided by the client — prevents double-submission.
    idempotency_key: Optional[uuid.UUID] = Field(
        default=None,
        description="Unique UUID per button click. Same key = same session_id returned."
    )


class FanoutResponse(BaseModel):
    """Returned immediately after a fan-out broadcast is initiated."""

    session_id: uuid.UUID = Field(description="Groups all referral rows for this fanout")
    notified_hotels: int = Field(description="Number of hotels that received a notification")
    status: str = Field(description="BROADCASTED | NO_AVAILABILITY | IDEMPOTENT")
    message: str


class ReferralStatusResponse(BaseModel):
    """Status of a single referral leg."""

    referral_id: uuid.UUID
    session_id: uuid.UUID
    destination_hotel_id: Optional[uuid.UUID]
    status: ReferralStatus
    handshake_code_hint: Optional[str] = Field(
        default=None,
        description="First 2 digits of the handshake code for display purposes"
    )
    accepted_at: Optional[str]
    completed_at: Optional[str]
    expired_at: Optional[str]


class SessionStatusResponse(BaseModel):
    """Summary of all referral legs belonging to one fan-out session."""

    session_id: uuid.UUID
    guest_name: str
    referrals: List[ReferralStatusResponse]
    accepted_count: int
    pending_count: int
