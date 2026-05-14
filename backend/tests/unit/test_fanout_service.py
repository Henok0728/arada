"""
Unit tests for the FanoutService.

Strategy: mock all I/O (DB, Redis, Celery) — test pure logic:
  - Only hotels WITH availability get notified.
  - Idempotency: second call with same key returns IDEMPOTENT status.
  - No availability → NO_AVAILABILITY response.
  - HMAC handshake code is attached to each referral row.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.referral import ReferralStatus, RoomType
from app.db.models.hotel import Hotel, HotelStatus, HotelCategory
from app.schemas.availability import HotelAvailabilityResponse, RoomAvailability
from app.schemas.referral import FanoutRequest


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def make_hotel(hotel_id=None, name="Test Hotel"):
    """Return a MagicMock that behaves like a Hotel ORM instance."""
    h = MagicMock()
    h.id = hotel_id or uuid.uuid4()
    h.name = name
    return h


def make_fanout_request(**overrides) -> FanoutRequest:
    base = dict(
        origin_hotel_id=uuid.uuid4(),
        guest_name="Dawit Bekele",
        guest_phone="+251911234567",
        room_type=RoomType.DOUBLE,
        party_size=2,
        origin_longitude=38.7578,
        origin_latitude=9.0227,
        radius_metres=5000.0,
        idempotency_key=uuid.uuid4(),
    )
    base.update(overrides)
    return FanoutRequest(**base)


def make_availability(hotel_id, room_type=RoomType.DOUBLE, count=3):
    return HotelAvailabilityResponse(
        hotel_id=hotel_id,
        updated_at=__import__("datetime").datetime.utcnow(),
        availability=[
            RoomAvailability(room_type=room_type, available_count=count)
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fanout_only_notifies_hotels_with_availability():
    """
    Given 2 nearby hotels — one with availability, one without —
    the fanout should notify exactly 1 hotel.
    """
    from app.services.fanout import execute_fanout

    hotel_with_avail = make_hotel(name="Hilton Addis")
    hotel_without_avail = make_hotel(name="Full House Hotel")
    req = make_fanout_request()

    # Patch the three I/O dependencies
    with (
        patch("app.services.fanout.HotelRepository") as MockHotelRepo,
        patch("app.services.fanout.ReferralRepository") as MockReferralRepo,
        patch("app.services.fanout.AvailabilityRepository") as MockAvailRepo,
        patch("app.services.fanout.demo_notify_task") as mock_notify,
    ):
        # Setup geo-lookup to return 2 hotels
        mock_hotel_repo = MockHotelRepo.return_value
        mock_hotel_repo.find_nearby_active = AsyncMock(
            return_value=[hotel_with_avail, hotel_without_avail]
        )

        # Setup availability: hotel_with_avail has rooms; hotel_without_avail has 0
        mock_avail_repo = MockAvailRepo.return_value
        mock_avail_repo.get_availability = AsyncMock(side_effect=[
            make_availability(hotel_with_avail.id),   # hotel 1: available
            make_availability(hotel_without_avail.id, count=0),  # hotel 2: full
        ])

        # Setup referral repo
        mock_referral_repo = MockReferralRepo.return_value
        mock_referral_repo.find_session_by_idempotency_key = AsyncMock(return_value=None)

        created_referral = MagicMock()
        created_referral.id = uuid.uuid4()
        created_referral.destination_hotel_id = hotel_with_avail.id
        created_referral.handshake_code = None
        created_referral.handshake_expires_at = None

        mock_referral_repo.create_fanout_batch = AsyncMock(return_value=[created_referral])

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        mock_notify.delay = MagicMock()

        result = await execute_fanout(db=mock_db, redis=mock_redis, req=req)

    assert result.status == "BROADCASTED"
    assert result.notified_hotels == 1, (
        "Only the hotel WITH availability should be notified"
    )
    # Verify the batch was called with only the available hotel's ID
    mock_referral_repo.create_fanout_batch.assert_called_once()
    call_kwargs = mock_referral_repo.create_fanout_batch.call_args.kwargs
    assert hotel_with_avail.id in call_kwargs["destination_hotel_ids"]
    assert hotel_without_avail.id not in call_kwargs["destination_hotel_ids"]

    # Verify Celery task was dispatched exactly once
    mock_notify.delay.assert_called_once()


@pytest.mark.asyncio
async def test_fanout_returns_no_availability_when_all_hotels_are_full():
    """All nearby hotels have 0 availability → NO_AVAILABILITY status."""
    from app.services.fanout import execute_fanout

    hotel = make_hotel()
    req = make_fanout_request()

    with (
        patch("app.services.fanout.HotelRepository") as MockHotelRepo,
        patch("app.services.fanout.ReferralRepository") as MockReferralRepo,
        patch("app.services.fanout.AvailabilityRepository") as MockAvailRepo,
        patch("app.services.fanout.demo_notify_task"),
    ):
        mock_hotel_repo = MockHotelRepo.return_value
        mock_hotel_repo.find_nearby_active = AsyncMock(return_value=[hotel])

        mock_avail_repo = MockAvailRepo.return_value
        mock_avail_repo.get_availability = AsyncMock(
            return_value=make_availability(hotel.id, count=0)
        )

        mock_referral_repo = MockReferralRepo.return_value
        mock_referral_repo.find_session_by_idempotency_key = AsyncMock(return_value=None)

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await execute_fanout(db=mock_db, redis=mock_redis, req=req)

    assert result.status == "NO_AVAILABILITY"
    assert result.notified_hotels == 0


@pytest.mark.asyncio
async def test_fanout_is_idempotent():
    """Sending the same idempotency_key twice returns IDEMPOTENT without creating DB rows."""
    from app.services.fanout import execute_fanout

    existing_session = uuid.uuid4()
    idem_key = uuid.uuid4()
    req = make_fanout_request(idempotency_key=idem_key)

    with (
        patch("app.services.fanout.HotelRepository") as MockHotelRepo,
        patch("app.services.fanout.ReferralRepository") as MockReferralRepo,
        patch("app.services.fanout.AvailabilityRepository"),
        patch("app.services.fanout.demo_notify_task"),
    ):
        mock_referral_repo = MockReferralRepo.return_value
        mock_referral_repo.find_session_by_idempotency_key = AsyncMock(
            return_value=existing_session  # Key already exists!
        )

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await execute_fanout(db=mock_db, redis=mock_redis, req=req)

    assert result.status == "IDEMPOTENT"
    assert result.session_id == existing_session
    # Hotel lookup should NOT have been called
    MockHotelRepo.return_value.find_nearby_active.assert_not_called()


@pytest.mark.asyncio
async def test_fanout_attaches_hmac_code_to_referral():
    """Each referral row must have a non-null handshake_code after fanout."""
    from app.services.fanout import execute_fanout

    hotel = make_hotel()
    req = make_fanout_request()

    with (
        patch("app.services.fanout.HotelRepository") as MockHotelRepo,
        patch("app.services.fanout.ReferralRepository") as MockReferralRepo,
        patch("app.services.fanout.AvailabilityRepository") as MockAvailRepo,
        patch("app.services.fanout.demo_notify_task"),
    ):
        mock_hotel_repo = MockHotelRepo.return_value
        mock_hotel_repo.find_nearby_active = AsyncMock(return_value=[hotel])

        mock_avail_repo = MockAvailRepo.return_value
        mock_avail_repo.get_availability = AsyncMock(
            return_value=make_availability(hotel.id, count=2)
        )

        mock_referral_repo = MockReferralRepo.return_value
        mock_referral_repo.find_session_by_idempotency_key = AsyncMock(return_value=None)

        referral = MagicMock()
        referral.id = uuid.uuid4()
        referral.destination_hotel_id = hotel.id
        referral.handshake_code = None
        referral.handshake_expires_at = None

        mock_referral_repo.create_fanout_batch = AsyncMock(return_value=[referral])

        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        await execute_fanout(db=mock_db, redis=mock_redis, req=req)

    # The service must have written a non-null hash to the referral object
    assert referral.handshake_code is not None, (
        "Fanout must attach HMAC handshake_code to every referral row"
    )
    assert referral.handshake_expires_at is not None, (
        "Fanout must set a handshake expiry on every referral row"
    )
    # Hash should be a 64-char hex string (SHA-256)
    assert len(referral.handshake_code) == 64


@pytest.mark.asyncio
async def test_fanout_returns_no_availability_when_no_hotels_found():
    """No hotels within radius → NO_AVAILABILITY, not a crash."""
    from app.services.fanout import execute_fanout

    req = make_fanout_request()

    with (
        patch("app.services.fanout.HotelRepository") as MockHotelRepo,
        patch("app.services.fanout.ReferralRepository") as MockReferralRepo,
        patch("app.services.fanout.AvailabilityRepository"),
        patch("app.services.fanout.demo_notify_task"),
    ):
        mock_hotel_repo = MockHotelRepo.return_value
        mock_hotel_repo.find_nearby_active = AsyncMock(return_value=[])

        mock_referral_repo = MockReferralRepo.return_value
        mock_referral_repo.find_session_by_idempotency_key = AsyncMock(return_value=None)

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await execute_fanout(db=mock_db, redis=mock_redis, req=req)

    assert result.status == "NO_AVAILABILITY"
    assert result.notified_hotels == 0
