"""
TenantManager — handles creation and management of per-hotel private schemas.

In the Lodge-Link hybrid multi-tenancy model:
  - `platform` schema holds shared data (hotels, users, referrals).
  - `hotel_{slug}` schema holds private, hotel-owned data (bookings, rates).

This service executes the raw DDL to bootstrap a new tenant's private space.
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def bootstrap_tenant_schema(db: AsyncSession, hotel_slug: str) -> bool:
    """
    Create a new PostgreSQL schema `hotel_{slug}` and initialize its tables.
    This is called during the hotel registration flow.
    """
    # Sanitize slug: only a-z, 0-9, and hyphen allowed (enforced by Pydantic schema)
    schema_name = f"hotel_{hotel_slug.replace('-', '_')}"

    try:
        # 1. Create the schema
        await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

        # 2. Create internal rate_configs table
        await db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.rate_configs (
                id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                room_type           TEXT NOT NULL,
                base_rate_etb       NUMERIC(10,2) NOT NULL,
                weekend_multiplier  NUMERIC(4,2) DEFAULT 1.0,
                seasonal_rules      JSONB,
                max_referral_discount NUMERIC(4,2) DEFAULT 0.0,
                updated_at          TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # 3. Create internal bookings table
        await db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.bookings (
                id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                referral_event_id   UUID,
                guest_name          TEXT,
                guest_phone         TEXT,
                room_number         TEXT,
                check_in            DATE NOT NULL,
                check_out           DATE NOT NULL,
                rate_etb            NUMERIC(10,2),
                source              TEXT CHECK (source IN ('direct', 'lodgelink_referral', 'walk_in')),
                created_at          TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # 4. Enable Row Level Security (RLS) on the private schema
        # This is a 'belt-and-suspenders' security layer.
        await db.execute(text(f"ALTER TABLE {schema_name}.bookings ENABLE ROW LEVEL SECURITY"))
        
        logger.info("Successfully bootstrapped tenant schema: %s", schema_name)
        return True

    except Exception as exc:
        logger.error("Failed to bootstrap tenant schema %s: %s", schema_name, exc)
        # We don't raise here — we let the main transaction handle the rollback
        # but we return False to signal failure.
        raise
