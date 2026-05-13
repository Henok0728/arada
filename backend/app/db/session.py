"""
Async SQLAlchemy engine and session factory.

Usage in route / service layer:
    async with get_db() as session:
        result = await session.execute(...)

Or via FastAPI dependency injection:
    async def endpoint(db: AsyncSession = Depends(get_db_session)):
        ...
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# `echo=False` in production — set DEBUG=True via env to see SQL logs.
# `pool_pre_ping=True` detects stale connections before use (important for RDS).
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # allows reading attributes after commit without re-query
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session and handles commit/rollback.

    Commits on clean exit; rolls back on any unhandled exception, then re-raises.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
