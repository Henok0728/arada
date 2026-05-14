"""
ReferralRepository — all DB queries specific to the Referral model.

Key responsibilities:
  - Create a batch of Referral rows (one per candidate hotel) sharing a session_id.
  - Query by session_id to poll fan-out status.
  - Idempotency check: if a session with this idempotency_key already exists,
    return the existing session_id without creating duplicates.
  - Expire PENDING referrals that have exceeded TTL (called by Celery task).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, select, update

from app.db.models.referral import Referral, ReferralStatus
from app.db.repositories.base import BaseRepository


class ReferralRepository(BaseRepository[Referral]):
    """Repository for Referral CRUD and fan-out specific queries."""

    model = Referral

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    async def find_session_by_idempotency_key(
        self, idempotency_key: UUID
    ) -> Optional[UUID]:
        """Return the existing session_id if a fanout with this key was already
        created. Returns None if this is a new request.

        The idempotency_key is stored in the `notes` field with a prefix so we
        don't need a new DB column — avoids a migration for a soft feature.
        """
        marker = f"idempotency:{idempotency_key}"
        result = await self.session.execute(
            select(Referral.session_id)
            .where(Referral.notes.contains(marker))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row

    # ------------------------------------------------------------------
    # Fan-out creation
    # ------------------------------------------------------------------

    async def create_fanout_batch(
        self,
        *,
        session_id: UUID,
        origin_hotel_id: UUID,
        guest_name: str,
        guest_phone: str,
        room_type: str,
        party_size: int,
        check_in_date: Optional[str],
        check_out_date: Optional[str],
        special_requests: Optional[str],
        destination_hotel_ids: Sequence[UUID],
        idempotency_key: Optional[UUID] = None,
    ) -> Sequence[Referral]:
        """Create one Referral row per destination hotel, all sharing session_id.

        Uses a single flush for performance — avoid N individual round-trips.
        """
        notes = f"idempotency:{idempotency_key}" if idempotency_key else None

        referrals = [
            Referral(
                session_id=session_id,
                origin_hotel_id=origin_hotel_id,
                destination_hotel_id=hotel_id,
                guest_name=guest_name,
                guest_phone=guest_phone,
                room_type=room_type,
                party_size=party_size,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                special_requests=special_requests,
                status=ReferralStatus.PENDING,
                notes=notes,
            )
            for hotel_id in destination_hotel_ids
        ]

        for referral in referrals:
            self.session.add(referral)

        await self.session.flush()
        for referral in referrals:
            await self.session.refresh(referral)

        return referrals

    # ------------------------------------------------------------------
    # Session queries
    # ------------------------------------------------------------------

    async def get_session_referrals(
        self, session_id: UUID
    ) -> Sequence[Referral]:
        """Return all Referral rows belonging to a fan-out session."""
        result = await self.session.execute(
            select(Referral).where(Referral.session_id == session_id)
        )
        return result.scalars().all()

    async def get_accepted_referral(
        self, session_id: UUID
    ) -> Optional[Referral]:
        """Return the first ACCEPTED referral in a session (if any)."""
        result = await self.session.execute(
            select(Referral).where(
                and_(
                    Referral.session_id == session_id,
                    Referral.status == ReferralStatus.ACCEPTED,
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    async def expire_stale_referrals(
        self, *, older_than: datetime
    ) -> int:
        """Mark all PENDING referrals older than `older_than` as EXPIRED.

        Called by the Celery beat task `expire_referrals_task`.
        Returns the number of rows updated.
        """
        result = await self.session.execute(
            update(Referral)
            .where(
                and_(
                    Referral.status == ReferralStatus.PENDING,
                    Referral.created_at < older_than,
                )
            )
            .values(
                status=ReferralStatus.EXPIRED,
                expired_at=datetime.now(timezone.utc).isoformat(),
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.flush()
        return result.rowcount
