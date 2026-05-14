"""
Referrals API router — POST /v1/referrals (fan-out) and GET/POST management endpoints.

Route design:
  POST /v1/referrals                    → Execute fan-out, returns session_id immediately.
  GET  /v1/referrals/{session_id}       → Poll session status (for receptionist UI).
  POST /v1/referrals/{id}/accept        → Destination hotel accepts (first-come-first-served).
  POST /v1/referrals/{id}/decline       → Destination hotel declines.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.availability import get_redis_client
from app.db.session import get_db_session
from app.db.models.referral import ReferralStatus
from app.db.repositories.referral import ReferralRepository
from app.schemas.referral import (
    FanoutRequest,
    FanoutResponse,
    ReferralStatusResponse,
    SessionStatusResponse,
)
from app.services import fanout as fanout_service
from app.workers.tasks import demo_notify_task

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas for accept/decline (simple, no separate schema file needed)
# ---------------------------------------------------------------------------

class DeclineRequest(BaseModel):
    reason: str | None = None


class AcceptResponse(BaseModel):
    referral_id: UUID
    status: str
    message: str


class DeclineResponse(BaseModel):
    referral_id: UUID
    status: str
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

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


@router.post(
    "/{referral_id}/accept",
    response_model=AcceptResponse,
    summary="Accept an incoming referral",
    description=(
        "Atomically marks this referral leg as ACCEPTED. "
        "If another hotel already accepted the same session, returns 409. "
        "Automatically declines all other pending legs in the same session "
        "and notifies the sender hotel via a demo Celery task."
    ),
)
async def accept_referral(
    referral_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> AcceptResponse:
    repo = ReferralRepository(db)

    # -----------------------------------------------------------------------
    # Load and validate the referral
    # -----------------------------------------------------------------------
    referral = await repo.get_by_id(referral_id)
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    # Guard: only PENDING referrals can be accepted
    if referral.status == ReferralStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This referral has expired. The guest may have already found accommodation.",
        )
    if referral.status == ReferralStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This referral has already been accepted.",
        )
    if referral.status != ReferralStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot accept a referral in state '{referral.status.value}'.",
        )

    # -----------------------------------------------------------------------
    # First-come-first-served: check if ANOTHER hotel already accepted this session
    # -----------------------------------------------------------------------
    existing_accept = await repo.get_accepted_referral(referral.session_id)
    if existing_accept and existing_accept.id != referral_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another hotel has already accepted this referral. The guest has been placed.",
        )

    # -----------------------------------------------------------------------
    # Atomic acceptance — within the same DB transaction (managed by session.py)
    # -----------------------------------------------------------------------
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Accept this leg
    await repo.update(referral, status=ReferralStatus.ACCEPTED, accepted_at=now_iso)

    # 2. Decline all other PENDING legs in this session (the ones we didn't accept)
    all_session_referrals = await repo.get_session_referrals(referral.session_id)
    for leg in all_session_referrals:
        if leg.id != referral_id and leg.status == ReferralStatus.PENDING:
            await repo.update(
                leg,
                status=ReferralStatus.DECLINED,
                declined_at=now_iso,
                decline_reason="Another hotel accepted first (auto-declined by fanout).",
            )

    # session.py handles commit on clean exit — no explicit db.commit() needed here.

    # -----------------------------------------------------------------------
    # Notify the sender hotel (fire-and-forget via Celery)
    # -----------------------------------------------------------------------
    demo_notify_task.delay(
        referral_id=str(referral.id),
        session_id=str(referral.session_id),
        guest_name=referral.guest_name,
        guest_phone=referral.guest_phone,
        destination_hotel_name="Accepting Hotel",
        handshake_code="[ACCEPTED — code generated at generation step]",
    )

    return AcceptResponse(
        referral_id=referral_id,
        status=ReferralStatus.ACCEPTED.value,
        message=(
            f"Referral accepted. Guest '{referral.guest_name}' is expected. "
            f"Show them the handshake code from the generate endpoint."
        ),
    )


@router.post(
    "/{referral_id}/decline",
    response_model=DeclineResponse,
    summary="Decline an incoming referral",
    description="Marks this specific referral leg as DECLINED. Other pending legs are unaffected.",
)
async def decline_referral(
    referral_id: UUID,
    req: DeclineRequest = None,
    db: AsyncSession = Depends(get_db_session),
) -> DeclineResponse:
    repo = ReferralRepository(db)

    referral = await repo.get_by_id(referral_id)
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    if referral.is_terminal():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot decline a referral in terminal state '{referral.status.value}'.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    await repo.update(
        referral,
        status=ReferralStatus.DECLINED,
        declined_at=now_iso,
        decline_reason=req.reason if req else None,
    )

    return DeclineResponse(
        referral_id=referral_id,
        status=ReferralStatus.DECLINED.value,
        message="Referral declined. Other hotels in the fan-out remain active.",
    )


@router.get(
    "/{referral_id}/handshake",
    response_model=HandshakeResponse,
    summary="Validate offline handshake code",
    description=(
        "Verifies a 6-character handshake code for a specific referral. "
        "If valid, marks the referral as COMPLETED."
    ),
)
async def validate_referral_handshake(
    referral_id: UUID,
    code: str,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
):
    from app.services import handshake as handshake_service
    from app.schemas.handshake import HandshakeResponse

    try:
        is_valid = await handshake_service.verify_handshake(db, redis, referral_id, code)
        if is_valid:
            return HandshakeResponse(
                success=True,
                message="Handshake verified successfully. Referral marked as COMPLETED."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid handshake code for this referral."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


