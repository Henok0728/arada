"""
Root test configuration and shared fixtures.

Test strategy:
  - Unit tests  (tests/unit/)      — pure logic, no DB, mock sessions
  - Integration tests (tests/integration/) — real asyncpg + test DB

pytest-asyncio is configured in asyncio_mode = "auto" via pyproject.toml
so every `async def test_*` runs under the event loop without extra decorators.

Shared fixtures defined here are available to ALL test modules.
"""
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base


# ---------------------------------------------------------------------------
# Event-loop policy (required for pytest-asyncio on Python 3.11 + Windows)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop_policy():
    """Use the default asyncio policy — explicit for cross-platform stability."""
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# In-memory SQLite engine for unit/repository tests that don't need PostGIS.
# For PostGIS-specific tests, use a real PostgreSQL DB (see integration/).
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def sqlite_engine():
    """Create a fresh in-memory SQLite engine per test function.

    SQLite is used for repository logic tests (CRUD, filters) that don't
    rely on PostGIS functions. PostGIS geo-radius tests require a real PG.
    """
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    # Create all tables defined in Base.metadata.
    # NOTE: PostGIS Geography columns are not supported by SQLite;
    # the hotel.location column is nullable so it is simply skipped here.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(sqlite_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean AsyncSession backed by the in-memory SQLite engine.

    Each test gets a fresh session. Rolls back after each test to ensure
    test isolation — no test should depend on data written by another test.
    """
    factory = async_sessionmaker(
        bind=sqlite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Mock session fixture (for pure unit tests that don't touch the DB at all)
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_session() -> MagicMock:
    """Return a MagicMock that looks like an AsyncSession.

    execute(), flush(), refresh(), add(), delete() are all AsyncMocks
    so `await session.execute(...)` works in tests without a real connection.
    """
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# Sample data helpers (used across unit + integration tests)
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_hotel_data() -> dict:
    """Minimal dict of valid hotel creation kwargs."""
    return {
        "name": "Sheraton Addis",
        "slug": "sheraton-addis",
        "country_code": "ET",
        "city": "Addis Ababa",
        "address": "Taitu Street, Addis Ababa",
        "phone_number": "+251111717171",
        "email": "reservations@sheraton-addis.example.com",
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Minimal dict of valid user creation kwargs (password pre-hashed)."""
    from app.services.auth import hash_password
    return {
        "email": "admin@sheraton-addis.example.com",
        "full_name": "Tigist Alemu",
        "hashed_password": hash_password("SecureP@ss123!"),
    }
