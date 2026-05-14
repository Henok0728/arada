"""add handshake fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-14 22:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('referrals', sa.Column('handshake_expires_at', sa.DateTime(timezone=True), nullable=True), schema='platform')
    op.add_column('referrals', sa.Column('is_handshake_verified', sa.Boolean(), server_default='false', nullable=False), schema='platform')


def downgrade() -> None:
    op.drop_column('referrals', 'is_handshake_verified', schema='platform')
    op.drop_column('referrals', 'handshake_expires_at', schema='platform')
