"""
Integration tests for HotelRepository against a real PostgreSQL + PostGIS DB.

These tests are SKIPPED automatically when the TEST_DATABASE_URL environment
variable is not set (e.g., in local dev without Docker). In CI, the GitHub
Actions workflow starts a postgres+postgis service container which provides
the URL.

Run locally with Docker:
    docker compose up -d db
    TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link_test \
        pytest backend/tests/integration/ -v

Important: Each test uses a transaction that is rolled back after the test
so the DB is left clean. No need to truncate tables between tests.
"""
import os
import uuid
<<<<<<< HEAD
from collections.abc import AsyncGenerator
=======
from typing import AsyncGenerator
>>>>>>> 8fb6c50cbe91c572732551f6fce39594ea0d8dc1

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.models.hotel import Hotel, HotelCategory, HotelStatus
from app.db.repositories.hotel import HotelRepository

# ---------------------------------------------------------------------------
# Skip all tests in this module when TEST_DATABASE_URL is not configured.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL not set — skipping integration tests",
)


# ---------------------------------------------------------------------------
# Per-module async engine (shared across all tests in this file)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    """Create a PostgreSQL engine and set up the platform schema for the module."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set")

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    # Ensure extensions and schema exist (migration must already be applied in CI)
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy", fromlist=["text"]).text(
                "CREATE SCHEMA IF NOT EXISTS platform"
            )
        )
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def pg_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transaction-wrapped session — rolled back after each test."""
    factory = async_sessionmaker(
        bind=pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def hotel_repo(pg_session: AsyncSession) -> HotelRepository:
    return HotelRepository(pg_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_hotel(**overrides) -> Hotel:
    uid = str(uuid.uuid4())[:8]
    defaults = {
        "name": f"Test Hotel {uid}",
        "slug": f"test-hotel-{uid}",
        "country_code": "ET",
        "city": "Addis Ababa",
        "address": f"Test Street {uid}",
        "phone_number": "+251911000001",
        "email": f"hotel-{uid}@example.com",
        "status": HotelStatus.ACTIVE,
        "category": HotelCategory.STANDARD,
        "is_referral_eligible": True,
    }
    defaults.update(overrides)
    return Hotel(**defaults)


# ===========================================================================
# CRUD integration tests
# ===========================================================================
class TestHotelCRUD:
    async def test_create_and_retrieve_hotel(self, hotel_repo: HotelRepository):
        hotel = _make_hotel(name="Sheraton Addis")
        created = await hotel_repo.create(hotel)

        assert created.id is not None
        assert created.name == "Sheraton Addis"
        assert created.status == HotelStatus.ACTIVE

        fetched = await hotel_repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    async def test_get_by_id_missing_returns_none(self, hotel_repo: HotelRepository):
        result = await hotel_repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_get_by_slug(self, hotel_repo: HotelRepository):
        hotel = _make_hotel(slug="unique-slug-int-test")
        await hotel_repo.create(hotel)

        found = await hotel_repo.get_by_slug("unique-slug-int-test")
        assert found is not None
        assert found.slug == "unique-slug-int-test"

    async def test_get_by_email(self, hotel_repo: HotelRepository):
        hotel = _make_hotel(email="integration@example.com")
        await hotel_repo.create(hotel)

        found = await hotel_repo.get_by_email("integration@example.com")
        assert found is not None

    async def test_update_hotel_name(self, hotel_repo: HotelRepository):
        hotel = _make_hotel()
        created = await hotel_repo.create(hotel)

        updated = await hotel_repo.update(created, name="Updated Name")
        assert updated.name == "Updated Name"

    async def test_delete_by_id(self, hotel_repo: HotelRepository):
        hotel = _make_hotel()
        created = await hotel_repo.create(hotel)

        deleted = await hotel_repo.delete_by_id(created.id)
        assert deleted is True

        gone = await hotel_repo.get_by_id(created.id)
        assert gone is None

    async def test_exists_true(self, hotel_repo: HotelRepository):
        hotel = _make_hotel()
        created = await hotel_repo.create(hotel)
        assert await hotel_repo.exists(created.id) is True

    async def test_exists_false(self, hotel_repo: HotelRepository):
        assert await hotel_repo.exists(uuid.uuid4()) is False

    async def test_count_increases_on_create(self, hotel_repo: HotelRepository):
        before = await hotel_repo.count()
        await hotel_repo.create(_make_hotel())
        await hotel_repo.create(_make_hotel())
        after = await hotel_repo.count()
        assert after == before + 2


# ===========================================================================
# Status transition integration tests
# ===========================================================================
class TestStatusTransitions:
    async def test_activate_from_sandbox(self, hotel_repo: HotelRepository):
        hotel = _make_hotel(status=HotelStatus.SANDBOX)
        created = await hotel_repo.create(hotel)

        activated = await hotel_repo.activate(created)
        assert activated.status == HotelStatus.ACTIVE
        assert activated.kyc_approved_at is not None

    async def test_suspend_active_hotel(self, hotel_repo: HotelRepository):
        hotel = _make_hotel(status=HotelStatus.ACTIVE)
        created = await hotel_repo.create(hotel)

        suspended = await hotel_repo.suspend(created)
        assert suspended.status == HotelStatus.SUSPENDED

    async def test_set_sandbox_from_pending_kyc(self, hotel_repo: HotelRepository):
        hotel = _make_hotel(status=HotelStatus.PENDING_KYC)
        created = await hotel_repo.create(hotel)

        sandboxed = await hotel_repo.set_sandbox(created)
        assert sandboxed.status == HotelStatus.SANDBOX


# ===========================================================================
# Slug / email uniqueness checks
# ===========================================================================
class TestUniquenessChecks:
    async def test_is_slug_taken_false_for_new_slug(self, hotel_repo: HotelRepository):
        result = await hotel_repo.is_slug_taken(f"brand-new-{uuid.uuid4()}")
        assert result is False

    async def test_is_slug_taken_true_after_create(self, hotel_repo: HotelRepository):
        slug = f"taken-slug-{uuid.uuid4()}"
        hotel = _make_hotel(slug=slug)
        await hotel_repo.create(hotel)

        assert await hotel_repo.is_slug_taken(slug) is True

    async def test_is_email_taken_false_for_new_email(self, hotel_repo: HotelRepository):
        result = await hotel_repo.is_email_taken(f"new-{uuid.uuid4()}@example.com")
        assert result is False

    async def test_is_email_taken_true_after_create(self, hotel_repo: HotelRepository):
        email = f"taken-{uuid.uuid4()}@example.com"
        hotel = _make_hotel(email=email)
        await hotel_repo.create(hotel)

        assert await hotel_repo.is_email_taken(email) is True


# ===========================================================================
# Active hotel filter
# ===========================================================================
class TestGetActiveHotels:
    async def test_returns_only_active_hotels(self, hotel_repo: HotelRepository):
        active = _make_hotel(status=HotelStatus.ACTIVE)
        suspended = _make_hotel(status=HotelStatus.SUSPENDED)

        await hotel_repo.create(active)
        await hotel_repo.create(suspended)

        results = await hotel_repo.get_active_hotels(country_code="ET")
        statuses = {h.status for h in results}
        assert HotelStatus.SUSPENDED not in statuses
        assert HotelStatus.ACTIVE in statuses

    async def test_filters_by_country_code(self, hotel_repo: HotelRepository):
        ke_hotel = _make_hotel(status=HotelStatus.ACTIVE, country_code="KE")
        await hotel_repo.create(ke_hotel)

        et_results = await hotel_repo.get_active_hotels(country_code="ET")
        for h in et_results:
            assert h.country_code == "ET"
