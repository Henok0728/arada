from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.db.session import get_db_session
from app.api.v1.availability import get_redis_client
from app.schemas.handshake import HandshakeGenerateRequest, HandshakeVerifyRequest, HandshakeResponse
from app.services import handshake as handshake_service

router = APIRouter()

@router.post(
    "/generate",
    response_model=HandshakeResponse,
    summary="Generate offline handshake code",
    description="Generates a 6-digit handshake code for an accepted referral and optionally sends it via SMS."
)
async def generate_handshake_endpoint(
    req: HandshakeGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client)
):
    try:
        code = await handshake_service.generate_handshake(db, redis, req.referral_id, req.phone_number)
        return HandshakeResponse(success=True, message=f"Handshake generated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post(
    "/verify",
    response_model=HandshakeResponse,
    summary="Verify offline handshake code",
    description="Verifies the 6-digit code against Redis or the database and marks the referral as completed."
)
async def verify_handshake_endpoint(
    req: HandshakeVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client)
):
    try:
        is_valid = await handshake_service.verify_handshake(db, redis, req.referral_id, req.code)
        if is_valid:
            return HandshakeResponse(success=True, message="Handshake verified successfully. Referral is now completed.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
