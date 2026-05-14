"""
Availability caching repository using Redis.
TTL is managed by core config settings.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.availability import RoomAvailability, HotelAvailabilityResponse

logger = logging.getLogger(__name__)


class AvailabilityRepository:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = settings.AVAILABILITY_CACHE_TTL_SECONDS

    def _get_key(self, hotel_id: UUID) -> str:
        return f"hotel:{hotel_id}:availability"

    async def get_availability(self, hotel_id: UUID) -> Optional[HotelAvailabilityResponse]:
        """Fetch current availability for a hotel from Redis."""
        key = self._get_key(hotel_id)
        data = await self.redis.get(key)
        
        if not data:
            return None
            
        try:
            parsed = json.loads(data)
            return HotelAvailabilityResponse(**parsed)
        except Exception as e:
            logger.error("Failed to parse availability for %s: %s", hotel_id, e)
            return None

    async def update_availability(
        self, hotel_id: UUID, availability: List[RoomAvailability]
    ) -> HotelAvailabilityResponse:
        """Update hotel availability in Redis with TTL."""
        response = HotelAvailabilityResponse(
            hotel_id=hotel_id,
            updated_at=datetime.now(timezone.utc),
            availability=availability
        )
        
        key = self._get_key(hotel_id)
        # Serialize model to JSON string
        data = response.model_dump_json()
        
        # Save to Redis with TTL
        await self.redis.setex(key, self.ttl, data)
        return response
