"""Fix plan updated_at: add missing column to platform.plans.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at to plans if it doesn't exist
    # Using a safe approach to avoid errors if it was partially created
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_schema='platform' AND table_name='plans' AND column_name='updated_at') THEN
                ALTER TABLE platform.plans ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
                UPDATE platform.plans SET updated_at = created_at;
                ALTER TABLE platform.plans ALTER COLUMN updated_at SET NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_column("plans", "updated_at", schema="platform")
