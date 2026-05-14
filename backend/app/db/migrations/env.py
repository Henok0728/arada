import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.models import Base  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
MANAGED_SCHEMAS = {"platform"}

def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "schema" and name not in MANAGED_SCHEMAS:
        return False
    if hasattr(obj, "schema") and obj.schema not in MANAGED_SCHEMAS:
        return False
    return True

def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        compare_type=True,
        version_table_schema="platform",
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
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
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # BUG FIX: Ensure the schema exists before Alembic tries to
        # write the version table to it.
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS platform"))
        await connection.commit()

        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    # BUG FIX: Better handling for nested loops in async environments
    try:
        asyncio.run(run_migrations_online())
    except RuntimeError:
        # Fallback for environments where a loop is already running
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_migrations_online())
