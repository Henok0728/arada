"""
Availability API router.
"""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.availability import AvailabilityUpdateRequest, HotelAvailabilityResponse
from app.db.repositories.availability import AvailabilityRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency for Redis client
async def get_redis_client() -> Redis:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def get_availability_repo(redis: Redis = Depends(get_redis_client)) -> AvailabilityRepository:
    return AvailabilityRepository(redis)


@router.get(
    "",
    response_model=list[HotelAvailabilityResponse],
    summary="Find nearby available hotels",
    description=(
        "Geospatially finds nearby hotels within a radius and returns their "
        "current room availability from the Redis cache. "
        "Hotels with NO cached availability are skipped."
    ),
)
async def query_nearby_availability(
    longitude: float,
    latitude: float,
    radius_metres: float = 5000.0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> list[HotelAvailabilityResponse]:
    from app.db.repositories.hotel import HotelRepository
    from app.db.repositories.availability import AvailabilityRepository

    hotel_repo = HotelRepository(db)
    avail_repo = AvailabilityRepository(redis)

    # 1. Geo-lookup (PostGIS)
    nearby_hotels = await hotel_repo.find_nearby_active(
        longitude=longitude,
        latitude=latitude,
        radius_metres=radius_metres,
        limit=limit,
    )

    if not nearby_hotels:
        return []

    # 2. Bulk fetch availability from Redis
    results = []
    for hotel in nearby_hotels:
        avail = await avail_repo.get_availability(hotel.id)
        if avail:
            results.append(avail)

    return results


@router.get(
    "/{hotel_id}/availability",
    response_model=HotelAvailabilityResponse,
    summary="Get hotel availability",
)
async def get_hotel_availability(
    hotel_id: UUID,
    repo: AvailabilityRepository = Depends(get_availability_repo)
):
    """
    Fetch the real-time availability for a specific hotel.
    Returns 404 if availability is not currently cached (stale).
    """
    availability = await repo.get_availability(hotel_id)
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found or expired for this hotel"
        )
    return availability


@router.post(
    "/{hotel_id}/availability",
    response_model=HotelAvailabilityResponse,
    summary="Update hotel availability",
)
async def update_hotel_availability(
    hotel_id: UUID,
    update_req: AvailabilityUpdateRequest,
    repo: AvailabilityRepository = Depends(get_availability_repo)
):
    """
    Update the real-time room availability for a hotel.
    This overwrites the existing cached availability and resets the TTL (90s).
    """
    return await repo.update_availability(hotel_id, update_req.availability)
