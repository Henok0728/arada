"""
HotelRepository — all DB queries specific to the Hotel model.

PostGIS-free implementation using standard SQL math filters for geographic 
radius lookups. This ensures the platform is portable across all cloud providers.
"""
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, select

from app.db.models.hotel import Hotel, HotelCategory, HotelStatus
from app.db.repositories.base import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    """Repository for Hotel CRUD and domain-specific queries."""

    model = Hotel

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    async def get_by_slug(self, slug: str) -> Optional[Hotel]:
        """Fetch a hotel by its unique URL slug. Returns None if absent."""
        result = await self.session.execute(
            select(Hotel).where(Hotel.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Hotel]:
        """Fetch a hotel by its registered email address."""
        result = await self.session.execute(
            select(Hotel).where(Hotel.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_hotels(
        self,
        *,
        country_code: str = "ET",
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Hotel]:
        """Return all ACTIVE, referral-eligible hotels for a country."""
        result = await self.session.execute(
            select(Hotel)
            .where(
                and_(
                    Hotel.status == HotelStatus.ACTIVE,
                    Hotel.is_referral_eligible.is_(True),
                    Hotel.country_code == country_code,
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Geo-radius query (core fanout lookup)
    # ------------------------------------------------------------------

    async def find_nearby_active(
        self,
        *,
        longitude: float,
        latitude: float,
        radius_metres: float = 5000.0,
        exclude_hotel_id: Optional[UUID] = None,
        category: Optional[HotelCategory] = None,
        limit: int = 20,
    ) -> Sequence[Hotel]:
        """Find ACTIVE, referral-eligible hotels within `radius_metres` of a point.

        Uses a standard SQL math filter to avoid the PostGIS extension dependency.
        """
        # Simple bounding box filter for performance
        # 1 degree of latitude is ~111km
        lat_delta = radius_metres / 111000.0
        # 1 degree of longitude is ~111km * cos(latitude)
        lng_delta = radius_metres / (111000.0 * 0.987) 
        
        filters = [
            Hotel.status == HotelStatus.ACTIVE,
            Hotel.is_referral_eligible.is_(True),
            Hotel.latitude.between(latitude - lat_delta, latitude + lat_delta),
            Hotel.longitude.between(longitude - lng_delta, longitude + lng_delta),
        ]

        if exclude_hotel_id is not None:
            filters.append(Hotel.id != exclude_hotel_id)

        if category is not None:
            filters.append(Hotel.category == category)

        result = await self.session.execute(
            select(Hotel)
            .where(and_(*filters))
            .limit(limit)
        )
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    async def activate(self, hotel: Hotel) -> Hotel:
        """Transition hotel from SANDBOX → ACTIVE (post-KYC approval)."""
        return await self.update(
            hotel,
            status=HotelStatus.ACTIVE,
            kyc_approved_at=datetime.now(timezone.utc).isoformat(),
        )

    async def suspend(self, hotel: Hotel) -> Hotel:
        """Suspend an ACTIVE hotel (policy violation)."""
        return await self.update(hotel, status=HotelStatus.SUSPENDED)

    async def set_sandbox(self, hotel: Hotel) -> Hotel:
        """Move hotel from PENDING_KYC → SANDBOX (documents received)."""
        return await self.update(hotel, status=HotelStatus.SANDBOX)

    # ------------------------------------------------------------------
    # Slug uniqueness check
    # ------------------------------------------------------------------

    async def is_slug_taken(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def is_email_taken(self, email: str) -> bool:
        return await self.get_by_email(email) is not None
