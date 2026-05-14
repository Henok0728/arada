"""
Declarative base and shared column mixins for all SQLAlchemy ORM models.

Every model inherits from `Base`. The `TimestampMixin` and `UUIDPrimaryKeyMixin`
are composed in where needed to avoid repetition.
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base.

    Using the new SQLAlchemy 2.0 `DeclarativeBase` style for full
    type-annotation support with `Mapped[]`.
    """
    pass


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID v4 primary key column named `id`."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Mixin that adds `created_at` / `updated_at` audit columns.

    `created_at` is set once by the DB server on INSERT.
    `updated_at` is refreshed on every UPDATE via `onupdate`.
    Both are stored as UTC timestamps with timezone info.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
