import pytest
from unittest.mock import AsyncMock, patch
import uuid
from datetime import datetime, timezone

from app.api.v1.availability import get_hotel_availability, update_hotel_availability
from app.schemas.availability import RoomAvailability, HotelAvailabilityResponse, AvailabilityUpdateRequest
from app.db.repositories.availability import AvailabilityRepository
from app.db.models.referral import RoomType
from fastapi import HTTPException

pytestmark = pytest.mark.asyncio

async def test_get_availability_repository():
    mock_redis = AsyncMock()
    # Mock redis get to return JSON data
    mock_redis.get.return_value = '{"hotel_id": "123e4567-e89b-12d3-a456-426614174000", "updated_at": "2026-05-14T20:00:00Z", "availability": [{"room_type": "DOUBLE", "available_count": 5}]}'
    
    repo = AvailabilityRepository(mock_redis)
    hotel_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    
    result = await repo.get_availability(hotel_id)
    assert result is not None
    assert result.hotel_id == hotel_id
    assert len(result.availability) == 1
    assert result.availability[0].room_type == RoomType.DOUBLE
    assert result.availability[0].available_count == 5

async def test_get_availability_empty_repository():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    repo = AvailabilityRepository(mock_redis)
    hotel_id = uuid.uuid4()
    
    result = await repo.get_availability(hotel_id)
    assert result is None

async def test_update_availability_repository():
    mock_redis = AsyncMock()
    repo = AvailabilityRepository(mock_redis)
    hotel_id = uuid.uuid4()
    
    availability = [RoomAvailability(room_type=RoomType.SINGLE, available_count=2)]
    
    result = await repo.update_availability(hotel_id, availability)
    
    assert result.hotel_id == hotel_id
    assert len(result.availability) == 1
    mock_redis.setex.assert_called_once()

async def test_get_hotel_availability_endpoint_success():
    mock_repo = AsyncMock()
    hotel_id = uuid.uuid4()
    
    mock_repo.get_availability.return_value = HotelAvailabilityResponse(
        hotel_id=hotel_id,
        updated_at=datetime.now(timezone.utc),
        availability=[RoomAvailability(room_type=RoomType.SUITE, available_count=1)]
    )
    
    result = await get_hotel_availability(hotel_id, repo=mock_repo)
    assert result.hotel_id == hotel_id
    assert len(result.availability) == 1

async def test_get_hotel_availability_endpoint_not_found():
    mock_repo = AsyncMock()
    hotel_id = uuid.uuid4()
    
    mock_repo.get_availability.return_value = None
    
    with pytest.raises(HTTPException) as excinfo:
        await get_hotel_availability(hotel_id, repo=mock_repo)
        
    assert excinfo.value.status_code == 404

async def test_update_hotel_availability_endpoint():
    mock_repo = AsyncMock()
    hotel_id = uuid.uuid4()
    
    update_req = AvailabilityUpdateRequest(
        availability=[RoomAvailability(room_type=RoomType.FAMILY, available_count=3)]
    )
    
    mock_repo.update_availability.return_value = HotelAvailabilityResponse(
        hotel_id=hotel_id,
        updated_at=datetime.now(timezone.utc),
        availability=update_req.availability
    )
    
    result = await update_hotel_availability(hotel_id, update_req, repo=mock_repo)
    assert result.hotel_id == hotel_id
    assert result.availability[0].room_type == RoomType.FAMILY
    assert result.availability[0].available_count == 3
