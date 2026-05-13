"""
Alembic migration environment — async SQLAlchemy setup.

Key decisions:
  1. Uses `run_sync` via SQLAlchemy's async engine adapter so Alembic's
     synchronous migration runner works with an asyncpg-backed engine.
  2. `include_schemas=True` + `include_object` filter ensures Alembic only
     manages objects in the `platform` schema (ignores PostGIS internal tables,
     public schema noise, etc.).
  3. The DB URL is injected from `app.core.config.settings` — never from
     alembic.ini — so no credentials appear in version control.
  4. `compare_type=True` detects column type changes on autogenerate.
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import create_async_engine

# ---------------------------------------------------------------------------
# Import all models so Base.metadata is fully populated before autogenerate.
# This is the single import that "teaches" Alembic about every table.
# ---------------------------------------------------------------------------
from app.db.models import Base  # noqa: F401 — side effect: registers all tables
from app.core.config import settings

# Alembic Config object provides access to values in alembic.ini
config = context.config

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the DB URL from pydantic-settings (NOT from alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Metadata target for autogenerate
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Schema filter — only manage objects in the `platform` schema.
# PostGIS stores its own tables in public; we don't want Alembic touching them.
# ---------------------------------------------------------------------------
MANAGED_SCHEMAS = {"platform"}


def include_object(obj, name, type_, reflected, compare_to):  # noqa: ANN
    """Filter function for autogenerate — skip non-platform schemas."""
    if type_ == "schema" and name not in MANAGED_SCHEMAS:
        return False
    if hasattr(obj, "schema") and obj.schema not in MANAGED_SCHEMAS:
        return False
    return True


# ---------------------------------------------------------------------------
# Offline migrations (alembic upgrade --sql)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL without connecting to the DB.
    Useful for audit, DBA review, or environments where direct DB access is restricted.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        compare_type=True,
        version_table_schema="platform",  # store alembic_version in platform schema
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (alembic upgrade head)
# ---------------------------------------------------------------------------
def do_run_migrations(connection) -> None:  # noqa: ANN
    """Synchronous migration runner called via run_sync inside async context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
        compare_type=True,
        version_table_schema="platform",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode against the live async database.

    Uses `run_sync` to bridge Alembic's synchronous migration API with
    SQLAlchemy's async connection model.
    """
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,  # no connection pooling during migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
