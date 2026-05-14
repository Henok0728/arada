"""
HotelRepository — all DB queries specific to the Hotel model.

Implements the Repository Pattern: services call methods here,
never raw SQLAlchemy in route handlers.

Key query: `find_nearby_active` uses PostGIS ST_DWithin with a GEOGRAPHY
column so distances are in metres on a WGS-84 spheroid — no CRS projection
needed. The GIST index on hotels.location makes this O(log n).
"""
from collections.abc import Sequence
from datetime import UTC
from uuid import UUID

from geoalchemy2 import Geography  # type: ignore[import]
from geoalchemy2.functions import ST_DWithin, ST_MakePoint  # type: ignore[import]
from sqlalchemy import and_, cast, select

from app.db.models.hotel import Hotel, HotelCategory, HotelStatus
from app.db.repositories.base import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    """Repository for Hotel CRUD and domain-specific queries."""

    model = Hotel

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    async def get_by_slug(self, slug: str) -> Hotel | None:
        """Fetch a hotel by its unique URL slug. Returns None if absent."""
        result = await self.session.execute(
            select(Hotel).where(Hotel.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Hotel | None:
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
        exclude_hotel_id: UUID | None = None,
        category: HotelCategory | None = None,
        limit: int = 20,
    ) -> Sequence[Hotel]:
        """Find ACTIVE, referral-eligible hotels within `radius_metres` of a point.

        Uses PostGIS ST_DWithin(geography, geography, metres) which correctly
        handles curvature of the Earth — critical near the equator (Ethiopia).
        The GIST index on hotels.location is used automatically.

        Args:
            longitude: WGS-84 longitude of the origin point.
            latitude:  WGS-84 latitude of the origin point.
            radius_metres: Search radius in metres (default 5 km).
            exclude_hotel_id: Optional UUID to exclude (the origin hotel itself).
            category: Filter by hotel category tier if provided.
            limit: Maximum number of results to return.

        Returns:
            Sequence of Hotel ORM objects ordered by proximity (nearest first).
        """
        # Build the origin point as a GEOGRAPHY cast so units are metres.
        origin = cast(
            ST_MakePoint(longitude, latitude),
            Geography(srid=4326),
        )

        filters = [
            Hotel.status == HotelStatus.ACTIVE,
            Hotel.is_referral_eligible.is_(True),
            Hotel.location.isnot(None),
            ST_DWithin(Hotel.location, origin, radius_metres),
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
        from datetime import datetime
        return await self.update(
            hotel,
            status=HotelStatus.ACTIVE,
            kyc_approved_at=datetime.now(UTC).isoformat(),
        )

    async def suspend(self, hotel: Hotel) -> Hotel:
        """Suspend an ACTIVE hotel (policy violation)."""
        return await self.update(hotel, status=HotelStatus.SUSPENDED)

    async def set_sandbox(self, hotel: Hotel) -> Hotel:
        """Move hotel from PENDING_KYC → SANDBOX (documents received)."""
        return await self.update(hotel, status=HotelStatus.SANDBOX)

    # ------------------------------------------------------------------
    # Slug uniqueness check (used during registration)
    # ------------------------------------------------------------------

    async def is_slug_taken(self, slug: str) -> bool:
        """Return True if the slug is already in use."""
        return await self.get_by_slug(slug) is not None

    async def is_email_taken(self, email: str) -> bool:
        """Return True if the email is already registered."""
        return await self.get_by_email(email) is not None
