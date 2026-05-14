"""
Referrals API router — POST /v1/referrals (fan-out) and GET /v1/referrals/{session_id}.

Route design:
  POST /v1/referrals          → Execute fan-out, returns session_id immediately.
  GET  /v1/referrals/{id}     → Poll session status (for receptionist UI).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.availability import get_redis_client
from app.db.session import get_db_session
from app.db.repositories.referral import ReferralRepository
from app.schemas.referral import (
    FanoutRequest,
    FanoutResponse,
    ReferralStatusResponse,
    SessionStatusResponse,
)
from app.db.models.referral import ReferralStatus
from app.services import fanout as fanout_service

router = APIRouter()


@router.post(
    "",
    response_model=FanoutResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate a referral fan-out",
    description=(
        "Geospatially finds nearby hotels with availability and concurrently "
        "notifies them. Returns immediately with a session_id. "
        "Idempotent: sending the same idempotency_key returns the existing session."
    ),
)
async def create_referral_fanout(
    req: FanoutRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> FanoutResponse:
    try:
        return await fanout_service.execute_fanout(db=db, redis=redis, req=req)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fanout failed: {exc}",
        ) from exc


@router.get(
    "/{session_id}",
    response_model=SessionStatusResponse,
    summary="Poll fan-out session status",
    description="Returns all referral legs for a session, including which hotel accepted.",
)
async def get_session_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> SessionStatusResponse:
    repo = ReferralRepository(db)
    referrals = await repo.get_session_referrals(session_id)

    if not referrals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No referrals found for session {session_id}",
        )

    legs = [
        ReferralStatusResponse(
            referral_id=r.id,
            session_id=r.session_id,
            destination_hotel_id=r.destination_hotel_id,
            status=r.status,
            # Expose first 2 chars of stored hash as a hint (not the code itself)
            handshake_code_hint=r.handshake_code[:2] if r.handshake_code else None,
            accepted_at=r.accepted_at,
            completed_at=r.completed_at,
            expired_at=r.expired_at,
        )
        for r in referrals
    ]

    return SessionStatusResponse(
        session_id=session_id,
        guest_name=referrals[0].guest_name,
        referrals=legs,
        accepted_count=sum(1 for r in referrals if r.status == ReferralStatus.ACCEPTED),
        pending_count=sum(1 for r in referrals if r.status == ReferralStatus.PENDING),
    )
