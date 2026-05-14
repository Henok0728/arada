"""Initial platform schema — hotels, users, api_keys, referrals.

Revision ID: 0001
Revises: None (initial)
Create Date: 2026-05-13

What this migration does:
  1. Creates the `platform` PostgreSQL schema.
  2. Enables the `postgis` extension (for GEOGRAPHY columns).
  3. Enables the `pgcrypto` extension (for gen_random_uuid() server default).
  4. Creates PostgreSQL ENUM types for hotel_category, hotel_status,
     user_role, referral_status, room_type (all namespaced to `platform`).
  5. Creates the four core tables: hotels, users, api_keys, referrals.
  6. Adds a GIST index on hotels.location for fast geo-radius queries.
  7. Enables Row Level Security (RLS) on users, api_keys, referrals.
     RLS policies are intentionally permissive for Phase 1 — Phase 2 will
     tighten them to hotel_id-scoped rows.

Downgrade removes all objects in reverse order to avoid FK constraint errors.
"""
from collections.abc import Sequence

import geoalchemy2  # noqa: F401 — registers Geography type with SQLAlchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Extensions (idempotent — safe to re-run)
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ------------------------------------------------------------------
    # 2. Platform schema
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")

    # ------------------------------------------------------------------
    # 3. PostgreSQL ENUM types (namespaced to platform schema)
    # ------------------------------------------------------------------
    hotel_category = postgresql.ENUM(
        "BUDGET", "STANDARD", "PREMIUM", "LUXURY",
        name="hotel_category", schema="platform", create_type=False,
    )
    hotel_category.create(op.get_bind(), checkfirst=True)

    hotel_status = postgresql.ENUM(
        "PENDING_KYC", "SANDBOX", "ACTIVE", "SUSPENDED",
        name="hotel_status", schema="platform", create_type=False,
    )
    hotel_status.create(op.get_bind(), checkfirst=True)

    user_role = postgresql.ENUM(
        "ADMIN", "RECEPTIONIST", "VIEWER",
        name="user_role", schema="platform", create_type=False,
    )
    user_role.create(op.get_bind(), checkfirst=True)

    referral_status = postgresql.ENUM(
        "PENDING", "ACCEPTED", "DECLINED", "COMPLETED", "EXPIRED", "CANCELLED",
        name="referral_status", schema="platform", create_type=False,
    )
    referral_status.create(op.get_bind(), checkfirst=True)

    room_type = postgresql.ENUM(
        "SINGLE", "DOUBLE", "TWIN", "SUITE", "FAMILY", "DORMITORY",
        name="room_type", schema="platform", create_type=False,
    )
    room_type.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # 4. platform.hotels
    # ------------------------------------------------------------------
    op.create_table(
        "hotels",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column(
            "country_code", sa.String(2), nullable=False, server_default="ET",
            comment="ISO 3166-1 alpha-2"
        ),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
            comment="PostGIS GEOGRAPHY(POINT, 4326) — WGS-84 lng/lat",
        ),
        sa.Column(
            "category",
            postgresql.ENUM(
                "BUDGET", "STANDARD", "PREMIUM", "LUXURY",
                name="hotel_category", schema="platform", create_type=False,
            ),
            nullable=False,
            server_default="STANDARD",
        ),
        sa.Column("stars", sa.Integer, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING_KYC", "SANDBOX", "ACTIVE", "SUSPENDED",
                name="hotel_status", schema="platform", create_type=False,
            ),
            nullable=False,
            server_default="PENDING_KYC",
        ),
        sa.Column("kyc_approved_at", sa.String, nullable=True),
        sa.Column("phone_number", sa.String(30), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column(
            "is_referral_eligible", sa.Boolean, nullable=False, server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="platform",
    )
    # Standard indexes
    op.create_index("ix_platform_hotels_slug", "hotels", ["slug"], schema="platform", unique=True)
    op.create_index("ix_platform_hotels_status", "hotels", ["status"], schema="platform")
    op.create_index("ix_platform_hotels_email", "hotels", ["email"], schema="platform", unique=True)

    # GIST index for PostGIS geo-radius queries (ST_DWithin)
    op.create_index(
        "ix_platform_hotels_location_gist",
        "hotels",
        ["location"],
        schema="platform",
        postgresql_using="gist",
    )

    # ------------------------------------------------------------------
    # 5. platform.users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "hotel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform.hotels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "ADMIN", "RECEPTIONIST", "VIEWER",
                name="user_role", schema="platform", create_type=False,
            ),
            nullable=False,
            server_default="RECEPTIONIST",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("last_login_at", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="platform",
    )
    op.create_index("ix_platform_users_email", "users", ["email"], schema="platform", unique=True)
    op.create_index("ix_platform_users_hotel_id", "users", ["hotel_id"], schema="platform")

    # Enable RLS (policies added in Phase 2 — permissive for Phase 1 MVP)
    op.execute("ALTER TABLE platform.users ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY platform_users_all ON platform.users USING (true) WITH CHECK (true)"
    )

    # ------------------------------------------------------------------
    # 6. platform.api_keys
    # ------------------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "hotel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform.hotels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "key_hash", sa.String(64), nullable=False, unique=True,
            comment="SHA-256 hex digest — never store plaintext key",
        ),
        sa.Column(
            "key_prefix", sa.String(20), nullable=False,
            comment="First 16 chars of plaintext key for UI identification",
        ),
        sa.Column("environment", sa.String(10), nullable=False, server_default="dev"),
        sa.Column(
            "scopes",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_used_at", sa.String, nullable=True),
        sa.Column("expires_at", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="platform",
    )
    op.create_index("ix_platform_api_keys_key_hash", "api_keys", ["key_hash"], schema="platform", unique=True)
    op.create_index("ix_platform_api_keys_hotel_id", "api_keys", ["hotel_id"], schema="platform")

    op.execute("ALTER TABLE platform.api_keys ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY platform_api_keys_all ON platform.api_keys USING (true) WITH CHECK (true)"
    )

    # ------------------------------------------------------------------
    # 7. platform.referrals
    # ------------------------------------------------------------------
    op.create_table(
        "referrals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Groups all Referral rows from a single fanout call",
        ),
        sa.Column(
            "origin_hotel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform.hotels.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "destination_hotel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform.hotels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("guest_name", sa.String(255), nullable=False),
        sa.Column(
            "guest_phone", sa.String(30), nullable=False,
            comment="E.164 format, e.g. +251911234567",
        ),
        sa.Column(
            "room_type",
            postgresql.ENUM(
                "SINGLE", "DOUBLE", "TWIN", "SUITE", "FAMILY", "DORMITORY",
                name="room_type", schema="platform", create_type=False,
            ),
            nullable=False,
            server_default="DOUBLE",
        ),
        sa.Column("check_in_date", sa.String(10), nullable=True),
        sa.Column("check_out_date", sa.String(10), nullable=True),
        sa.Column("party_size", sa.Integer, nullable=False, server_default="1"),
        sa.Column("special_requests", sa.Text, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "ACCEPTED", "DECLINED", "COMPLETED", "EXPIRED", "CANCELLED",
                name="referral_status", schema="platform", create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("handshake_code", sa.String(64), nullable=True),
        sa.Column("handshake_validated_at", sa.String, nullable=True),
        sa.Column("accepted_at", sa.String, nullable=True),
        sa.Column("declined_at", sa.String, nullable=True),
        sa.Column("completed_at", sa.String, nullable=True),
        sa.Column("expired_at", sa.String, nullable=True),
        sa.Column("cancelled_at", sa.String, nullable=True),
        sa.Column("decline_reason", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="platform",
    )
    op.create_index("ix_platform_referrals_session_id", "referrals", ["session_id"], schema="platform")
    op.create_index("ix_platform_referrals_status", "referrals", ["status"], schema="platform")
    op.create_index("ix_platform_referrals_origin_hotel_id", "referrals", ["origin_hotel_id"], schema="platform")
    op.create_index("ix_platform_referrals_destination_hotel_id", "referrals", ["destination_hotel_id"], schema="platform")
    op.create_index("ix_platform_referrals_handshake_code", "referrals", ["handshake_code"], schema="platform")

    op.execute("ALTER TABLE platform.referrals ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY platform_referrals_all ON platform.referrals USING (true) WITH CHECK (true)"
    )


def downgrade() -> None:
    # Reverse order: dependents first, then dependencies.

    # Tables (FKs point up the list)
    op.execute("DROP TABLE IF EXISTS platform.referrals CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.api_keys CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.users CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.hotels CASCADE")

    # ENUM types
    for enum_name in (
        "room_type", "referral_status", "user_role", "hotel_status", "hotel_category"
    ):
        op.execute(f"DROP TYPE IF EXISTS platform.{enum_name} CASCADE")

    # Schema (only if empty; drop cascade to be safe in dev)
    op.execute("DROP SCHEMA IF EXISTS platform CASCADE")

    # Leave extensions — they may be used by other applications on this DB cluster.
