"""
Generic async BaseRepository[T] using the Repository Pattern.

Design rationale:
  - All DB queries live in repositories, NEVER in route handlers or services.
  - Repositories receive an AsyncSession via constructor injection (not DI magic)
    so they are easily unit-testable with a mock session.
  - Generic typing (`ModelType`) allows IDE autocomplete and type-checking on
    all concrete repositories without repeating CRUD boilerplate.
  - Every method is `async` — mandatory for asyncpg-backed sessions.

Usage:
    class HotelRepository(BaseRepository[Hotel]):
        model = Hotel
"""
from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """CRUD repository base class.

    Subclasses MUST define:
        model: Type[ModelType]  — the SQLAlchemy ORM model class
    """

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        """Inject the async session — one session per request lifecycle."""
        self.session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_id(self, record_id: UUID) -> ModelType | None:
        """Fetch a single record by primary key. Returns None if not found."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, record_id: UUID) -> ModelType:
        """Fetch by PK; raise ValueError if not found (callers map to HTTP 404)."""
        obj = await self.get_by_id(record_id)
        if obj is None:
            raise ValueError(
                f"{self.model.__name__} with id={record_id} not found"
            )
        return obj

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Return a paginated list of all records (no filters)."""
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        """Return total row count for the model's table."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def exists(self, record_id: UUID) -> bool:
        """Return True if a record with the given ID exists."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(
                self.model.id == record_id
            )
        )
        return result.scalar_one() > 0

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(self, obj: ModelType) -> ModelType:
        """Persist a new model instance. Flushes to get DB-generated values
        (e.g., server_default UUID and timestamps) without committing.

        The session commit is handled by the request lifecycle in session.py.
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        """Apply keyword argument updates to an existing model instance."""
        for field, value in kwargs.items():
            setattr(obj, field, value)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        """Permanently delete a model instance from the database."""
        await self.session.delete(obj)
        await self.session.flush()

    async def delete_by_id(self, record_id: UUID) -> bool:
        """Delete by PK. Returns True if record existed and was deleted."""
        obj = await self.get_by_id(record_id)
        if obj is None:
            return False
        await self.delete(obj)
        return True
