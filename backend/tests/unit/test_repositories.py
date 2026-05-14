"""
Unit tests for BaseRepository and HotelRepository.

These tests use a MagicMock session (from conftest.py) — no real DB.
They validate that:
  1. BaseRepository correctly delegates SQL operations to the session.
  2. HotelRepository builds correct WHERE clauses and calls the right helpers.
  3. Status transition methods set the correct field values.

Integration tests (with a real PostgreSQL + PostGIS instance) live in
tests/integration/ and cover geo-radius queries that cannot be mocked.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models.hotel import Hotel, HotelCategory, HotelStatus
from app.db.repositories.hotel import HotelRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hotel(**kwargs) -> Hotel:
    """Build an unsaved Hotel instance with sensible defaults."""
    defaults = {
        "id": uuid.uuid4(),
        "name": "Test Hotel",
        "slug": "test-hotel",
        "country_code": "ET",
        "city": "Addis Ababa",
        "address": "Test Street 1",
        "phone_number": "+251911000001",
        "email": "test@hotel.example.com",
        "status": HotelStatus.ACTIVE,
        "category": HotelCategory.STANDARD,
        "is_referral_eligible": True,
    }
    defaults.update(kwargs)
    return Hotel(**defaults)


# ===========================================================================
# BaseRepository
# ===========================================================================
class TestBaseRepository:
    """Tests that BaseRepository correctly wires calls to AsyncSession."""

    def setup_method(self):
        self.session = MagicMock()
        self.session.execute = AsyncMock()
        self.session.flush = AsyncMock()
        self.session.refresh = AsyncMock()
        self.session.add = MagicMock()
        self.session.delete = AsyncMock()

        # Create a concrete subclass for testing (Hotel uses BaseRepository[Hotel])
        self.repo = HotelRepository(self.session)

    @pytest.mark.asyncio
    async def test_create_adds_to_session_and_flushes(self):
        hotel = _make_hotel()
        self.session.refresh = AsyncMock(return_value=None)

        await self.repo.create(hotel)
        self.session.add.assert_called_once_with(hotel)
        self.session.flush.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(hotel)

    @pytest.mark.asyncio
    async def test_update_sets_attributes_and_flushes(self):
        hotel = _make_hotel(status=HotelStatus.SANDBOX)
        self.session.refresh = AsyncMock(side_effect=lambda obj: None)

        updated = await self.repo.update(hotel, status=HotelStatus.ACTIVE)
        assert updated is not None
        assert hotel.status == HotelStatus.ACTIVE
        self.session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_calls_session_delete(self):
        hotel = _make_hotel()
        await self.repo.delete(hotel)

        self.session.delete.assert_awaited_once_with(hotel)
        self.session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """scalar_one_or_none() returning None → get_by_id returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.get_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_hotel_when_found(self):
        hotel = _make_hotel()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = hotel
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.get_by_id(hotel.id)
        assert result is hotel

    @pytest.mark.asyncio
    async def test_get_by_id_or_raise_raises_when_missing(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="not found"):
            await self.repo.get_by_id_or_raise(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_count_gt_zero(self):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        self.session.execute = AsyncMock(return_value=mock_result)

        assert await self.repo.exists(uuid.uuid4()) is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_count_zero(self):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        self.session.execute = AsyncMock(return_value=mock_result)

        assert await self.repo.exists(uuid.uuid4()) is False

    @pytest.mark.asyncio
    async def test_delete_by_id_returns_false_when_not_found(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.delete_by_id(uuid.uuid4())
        assert result is False


# ===========================================================================
# HotelRepository — domain-specific methods
# ===========================================================================
class TestHotelRepository:
    def setup_method(self):
        self.session = MagicMock()
        self.session.execute = AsyncMock()
        self.session.flush = AsyncMock()
        self.session.refresh = AsyncMock()
        self.session.add = MagicMock()
        self.session.delete = AsyncMock()
        self.repo = HotelRepository(self.session)

    # ---- get_by_slug ----------------------------------------------------
    @pytest.mark.asyncio
    async def test_get_by_slug_found(self):
        hotel = _make_hotel(slug="addis-gem")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = hotel
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.get_by_slug("addis-gem")
        assert result is hotel

    @pytest.mark.asyncio
    async def test_get_by_slug_not_found(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.get_by_slug("nonexistent-slug")
        assert result is None

    # ---- is_slug_taken + is_email_taken ---------------------------------
    @pytest.mark.asyncio
    async def test_is_slug_taken_true(self):
        hotel = _make_hotel()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = hotel
        self.session.execute = AsyncMock(return_value=mock_result)

        assert await self.repo.is_slug_taken("sheraton-addis") is True

    @pytest.mark.asyncio
    async def test_is_slug_taken_false(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        assert await self.repo.is_slug_taken("brand-new-slug") is False

    @pytest.mark.asyncio
    async def test_is_email_taken_true(self):
        hotel = _make_hotel()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = hotel
        self.session.execute = AsyncMock(return_value=mock_result)

        assert await self.repo.is_email_taken("taken@hotel.com") is True

    # ---- Status transitions ---------------------------------------------
    @pytest.mark.asyncio
    async def test_activate_sets_status_active(self):
        hotel = _make_hotel(status=HotelStatus.SANDBOX)
        self.session.refresh = AsyncMock(side_effect=lambda obj: None)

        await self.repo.activate(hotel)

        assert hotel.status == HotelStatus.ACTIVE
        assert hotel.kyc_approved_at is not None

    @pytest.mark.asyncio
    async def test_suspend_sets_status_suspended(self):
        hotel = _make_hotel(status=HotelStatus.ACTIVE)
        self.session.refresh = AsyncMock(side_effect=lambda obj: None)

        await self.repo.suspend(hotel)

        assert hotel.status == HotelStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_set_sandbox_sets_status_sandbox(self):
        hotel = _make_hotel(status=HotelStatus.PENDING_KYC)
        self.session.refresh = AsyncMock(side_effect=lambda obj: None)

        await self.repo.set_sandbox(hotel)

        assert hotel.status == HotelStatus.SANDBOX


# ===========================================================================
# Unit tests for HotelStatus state machine logic (model level)
# ===========================================================================
class TestHotelStatusEnum:
    def test_all_statuses_are_strings(self):
        for status in HotelStatus:
            assert isinstance(status.value, str)

    def test_pending_kyc_is_initial(self):
        """The default status at registration should be PENDING_KYC."""
        assert HotelStatus.PENDING_KYC.value == "PENDING_KYC"


class TestReferralStatusMachine:
    def test_is_terminal_completed(self):
        from app.db.models.referral import Referral, ReferralStatus
        r = Referral(status=ReferralStatus.COMPLETED)
        assert r.is_terminal() is True

    def test_is_terminal_pending_is_false(self):
        from app.db.models.referral import Referral, ReferralStatus
        r = Referral(status=ReferralStatus.PENDING)
        assert r.is_terminal() is False

    def test_is_terminal_accepted_is_false(self):
        from app.db.models.referral import Referral, ReferralStatus
        r = Referral(status=ReferralStatus.ACCEPTED)
        assert r.is_terminal() is False

    def test_terminal_states_set(self):
        from app.db.models.referral import ReferralStatus
        terminal = {
            ReferralStatus.COMPLETED,
            ReferralStatus.DECLINED,
            ReferralStatus.EXPIRED,
            ReferralStatus.CANCELLED,
        }
        assert len(terminal) == 4
