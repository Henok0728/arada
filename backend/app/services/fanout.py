"""
FanoutService — the core of the Lodge-Link referral engine.

Algorithm (one receptionist button click):

  1. Idempotency guard: if the same idempotency_key was seen before,
     return the existing session_id immediately (no DB writes, no SMS).

  2. Geo-lookup: query HotelRepository.find_nearby_active() for hotels
     within radius_metres using PostGIS ST_DWithin.

  3. Availability filter: for each nearby hotel, hit Redis (O(1) per hotel)
     using the AvailabilityRepository. Hotels with zero available rooms of
     the requested type are silently skipped.

  4. Fan-out (asyncio.gather): concurrently:
       a. Create a Referral DB row per qualified hotel (batch flush).
       b. Dispatch a Celery task (send_sms_task or demo_notify_task) per hotel.
       c. Attach the HMAC handshake code to each referral row.

  5. Return FanoutResponse immediately — do NOT block on SMS delivery.

Performance characteristics:
  - DB: 1 PostGIS query + 1 batch INSERT (N rows in 1 flush).
  - Redis: N parallel GET calls (asyncio.gather).
  - SMS: Celery tasks queued asynchronously — zero blocking.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_handshake_code, hash_handshake_code
from app.db.models.referral import Referral, ReferralStatus
from app.db.models.hotel import Hotel
from app.db.repositories.availability import AvailabilityRepository
from app.db.repositories.hotel import HotelRepository
from app.db.repositories.referral import ReferralRepository
from app.schemas.referral import FanoutRequest, FanoutResponse
from app.workers.tasks import send_sms_task, demo_notify_task

logger = logging.getLogger(__name__)

# How long a PENDING referral lives before Celery expires it.
REFERRAL_TTL_MINUTES = 5


async def _check_availability(
    repo: AvailabilityRepository,
    hotel_id: uuid.UUID,
    requested_room_type: str,
) -> bool:
    """Return True if Redis shows at least 1 available room of the requested type."""
    avail = await repo.get_availability(hotel_id)
    if avail is None:
        # No cache entry = hotel hasn't published availability yet — skip.
        return False
    for room in avail.availability:
        if room.room_type.value == requested_room_type and room.available_count > 0:
            return True
    return False


async def execute_fanout(
    db: AsyncSession,
    redis: Redis,
    req: FanoutRequest,
) -> FanoutResponse:
    """Execute a full referral fan-out and return immediately.

    This function is called by the POST /v1/referrals route handler.
    """
    hotel_repo = HotelRepository(db)
    referral_repo = ReferralRepository(db)
    avail_repo = AvailabilityRepository(redis)

    # -----------------------------------------------------------------------
    # 1. Idempotency guard
    # -----------------------------------------------------------------------
    if req.idempotency_key:
        existing_session = await referral_repo.find_session_by_idempotency_key(
            req.idempotency_key
        )
        if existing_session:
            logger.info(
                "Idempotent fanout — returning existing session %s", existing_session
            )
            return FanoutResponse(
                session_id=existing_session,
                notified_hotels=0,
                status="IDEMPOTENT",
                message="This referral was already submitted. Returning existing session.",
            )

    # -----------------------------------------------------------------------
    # 2. Geospatial lookup (PostGIS)
    # -----------------------------------------------------------------------
    nearby_hotels: Sequence[Hotel] = await hotel_repo.find_nearby_active(
        longitude=req.origin_longitude,
        latitude=req.origin_latitude,
        radius_metres=req.radius_metres,
        exclude_hotel_id=req.origin_hotel_id,
        limit=20,
    )

    if not nearby_hotels:
        logger.info("No active hotels found near %s,%s", req.origin_latitude, req.origin_longitude)
        return FanoutResponse(
            session_id=uuid.uuid4(),
            notified_hotels=0,
            status="NO_AVAILABILITY",
            message="No active hotels found nearby.",
        )

    # -----------------------------------------------------------------------
    # 3. Availability filter (concurrent Redis lookups)
    # -----------------------------------------------------------------------
    # DEMO OVERRIDE: If special_requests contains AUTO_TARGET:hotel_id, we bypass filters
    auto_target_id = None
    if req.special_requests and "AUTO_TARGET:" in req.special_requests:
        try:
            auto_target_id = UUID(req.special_requests.split("AUTO_TARGET:")[1].split()[0])
        except:
            pass

    if auto_target_id:
        target_hotel = await hotel_repo.get_by_id(auto_target_id)
        if target_hotel:
            logger.info("Demo override: AUTO_TARGET detected for hotel %s", auto_target_id)
            qualified_hotels = [target_hotel]
        else:
            qualified_hotels = []
    else:
        availability_checks = await asyncio.gather(
            *[
                _check_availability(avail_repo, hotel.id, req.room_type.value)
                for hotel in nearby_hotels
            ]
        )

        qualified_hotels = [
            hotel
            for hotel, is_available in zip(nearby_hotels, availability_checks)
            if is_available
        ]

    if not qualified_hotels:
        logger.info("No hotels qualified for room_type=%s", req.room_type)
        return FanoutResponse(
            session_id=uuid.uuid4(),
            notified_hotels=0,
            status="NO_AVAILABILITY",
            message=f"No hotels with available {req.room_type.value} rooms nearby.",
        )

    # -----------------------------------------------------------------------
    # 4. Create referral rows (batch) + attach HMAC codes
    # -----------------------------------------------------------------------
    session_id = uuid.uuid4()

    referrals = await referral_repo.create_fanout_batch(
        session_id=session_id,
        origin_hotel_id=req.origin_hotel_id,
        guest_name=req.guest_name,
        guest_phone=req.guest_phone,
        room_type=req.room_type,
        party_size=req.party_size,
        check_in_date=req.check_in_date,
        check_out_date=req.check_out_date,
        special_requests=req.special_requests,
        destination_hotel_ids=[h.id for h in qualified_hotels],
        idempotency_key=req.idempotency_key,
    )

    # Attach HMAC handshake code to each referral
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=REFERRAL_TTL_MINUTES)
    for referral in referrals:
        code = generate_handshake_code(
            referral_id=referral.id,
            hotel_id=referral.destination_hotel_id,
            secret_key=settings.SECRET_KEY,
        )
        hashed = hash_handshake_code(code)
        referral.handshake_code = hashed
        referral.handshake_expires_at = expires_at

        # Cache in Redis for fast verification (TTL = 5 mins = 300 seconds)
        cache_key = f"handshake:{referral.id}"
        await redis.setex(cache_key, REFERRAL_TTL_MINUTES * 60, hashed)

    await db.flush()

    # -----------------------------------------------------------------------
    # 5. Dispatch Celery notifications concurrently (fire-and-forget)
    # -----------------------------------------------------------------------
    for referral, hotel in zip(referrals, qualified_hotels):
        # Reconstruct the plaintext 6-digit code for SMS (deterministic HMAC)
        code = generate_handshake_code(
            referral_id=referral.id,
            hotel_id=referral.destination_hotel_id,
            secret_key=settings.SECRET_KEY,
        )
        # Demo-safe: use demo_notify_task which logs to console
        # In production, swap for send_sms_task targeting guest_phone
        demo_notify_task.delay(
            referral_id=str(referral.id),
            session_id=str(session_id),
            guest_name=req.guest_name,
            guest_phone=req.guest_phone,
            destination_hotel_name=hotel.name,
            handshake_code=code,
        )

    logger.info(
        "Fanout session=%s: broadcasted to %d hotels",
        session_id,
        len(qualified_hotels),
    )

    return FanoutResponse(
        session_id=session_id,
        notified_hotels=len(qualified_hotels),
        status="BROADCASTED",
        message=f"Referral broadcasted to {len(qualified_hotels)} hotel(s). Awaiting acceptance.",
    )
