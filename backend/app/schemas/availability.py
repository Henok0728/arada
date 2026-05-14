"""
Availability Pydantic schemas for API validation.
"""
from typing import List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.db.models.referral import RoomType


class RoomAvailability(BaseModel):
    room_type: RoomType
    available_count: int = Field(ge=0, description="Number of available rooms of this type")


class AvailabilityUpdateRequest(BaseModel):
    availability: List[RoomAvailability]


class HotelAvailabilityResponse(BaseModel):
    hotel_id: UUID
    updated_at: datetime
    availability: List[RoomAvailability]
