import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.referral import Referral, ReferralStatus
from app.core.security import generate_handshake_code, hash_handshake_code
from app.core.config import settings
from app.workers.tasks import send_sms_task

logger = logging.getLogger(__name__)

async def generate_handshake(
    db: AsyncSession,
    redis: Redis,
    referral_id: UUID,
    phone_number: str | None = None
) -> str:
    """
    Generate a handshake code, store hash in DB and Redis, and optionally SMS.
    """
    # Verify referral exists and is ACCEPTED
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
        
    if referral.status != ReferralStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Referral must be in ACCEPTED state to generate a handshake"
        )
        
    if not referral.destination_hotel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Referral destination hotel is not set"
        )

    # Generate 6-digit code using HMAC
    code = generate_handshake_code(
        referral_id=referral.id,
        hotel_id=referral.destination_hotel_id,
        secret_key=settings.SECRET_KEY
    )
    
    # Hash for storage
    hashed_code = hash_handshake_code(code)
    
    # Expiration (15 mins TTL)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Update DB
    referral.handshake_code = hashed_code
    referral.handshake_expires_at = expires_at
    await db.commit()
    
    # Cache in Redis for fast lookup (15 mins = 900 seconds)
    try:
        cache_key = f"handshake:{referral_id}"
        await redis.setex(cache_key, 900, hashed_code)
    except Exception as e:
        logger.error(f"Failed to cache handshake in Redis: {e}")
    
    # Send SMS if phone number provided
    if phone_number:
        message = f"Your Lodge-Link Handshake Code is: {code}. Show this at the hotel reception."
        # Call Celery task asynchronously (fails gracefully if Redis is down)
        try:
            send_sms_task.delay(phone_number, message)
        except Exception as e:
            logger.error(f"Failed to queue handshake SMS: {e}")
        
    return code


async def verify_handshake(
    db: AsyncSession,
    redis: Redis,
    referral_id: UUID,
    code: str
) -> bool:
    """
    Verify the 6-digit code against Redis (fast path) or DB (slow path).
    """
    hashed_input = hash_handshake_code(code)
    
    # Fast path: Check Redis
    cache_key = f"handshake:{referral_id}"
    cached_hash = await redis.get(cache_key)
    
    is_valid = False
    
    if cached_hash:
        if cached_hash == hashed_input:
            is_valid = True
    else:
        # Slow path: Check DB
        result = await db.execute(select(Referral).where(Referral.id == referral_id))
        referral = result.scalar_one_or_none()
        
        if not referral:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
            
        if not referral.handshake_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No handshake generated for this referral")
            
        if referral.handshake_expires_at:
            if datetime.now(timezone.utc) > referral.handshake_expires_at:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Handshake code has expired")
                
        if referral.handshake_code == hashed_input:
            is_valid = True
            
    if is_valid:
        # Update Referral state
        result = await db.execute(select(Referral).where(Referral.id == referral_id))
        referral = result.scalar_one_or_none()
        
        if referral:
            if referral.status in {ReferralStatus.COMPLETED, ReferralStatus.CANCELLED, ReferralStatus.DECLINED, ReferralStatus.EXPIRED}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referral is in terminal state")
            referral.status = ReferralStatus.COMPLETED
            referral.is_handshake_verified = True
            referral.handshake_validated_at = datetime.now(timezone.utc).isoformat()
            referral.completed_at = datetime.now(timezone.utc).isoformat()
            await db.commit()
            
            # Clean up Redis
            await redis.delete(cache_key)
            return True
            
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid handshake code")
