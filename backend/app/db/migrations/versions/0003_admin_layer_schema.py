"""Admin layer schema: plans, audit_log, and hotel fields.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create platform.plans table
    op.create_table(
        "plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("price_etb", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_referrals_per_month", sa.Integer, nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
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

    # Create platform.audit_log table
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="platform",
    )

    # Add columns to platform.hotels
    op.add_column(
        "hotels",
        sa.Column("is_platform_admin", sa.Boolean(), server_default="false", nullable=False),
        schema="platform"
    )
    op.add_column(
        "hotels",
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="platform"
    )

    # Seed default plans
    op.execute("""
        INSERT INTO platform.plans (name, display_name, price_etb, max_referrals_per_month, commission_rate, features)
        VALUES 
        ('starter', 'Starter', 0.00, 50, 0.025, '{"sms": false, "analytics": false, "corridor_access": false, "priority_support": false}'),
        ('growth', 'Growth', 499.00, 300, 0.015, '{"sms": true, "analytics": true, "corridor_access": false, "priority_support": false}'),
        ('enterprise', 'Enterprise', NULL, NULL, 0.010, '{"sms": true, "analytics": true, "corridor_access": true, "priority_support": true}')
        ON CONFLICT (name) DO NOTHING;
    """)

    # We cannot set the default plan for existing hotels here because the UUIDs of the plans are generated randomly.
    # We will let the seed script or application handle assigning plan_ids.


def downgrade() -> None:
    op.drop_column("hotels", "plan_id", schema="platform")
    op.drop_column("hotels", "is_platform_admin", schema="platform")
    op.drop_table("audit_log", schema="platform")
    op.drop_table("plans", schema="platform")
