"""add_pnl_audit_strategy

Revision ID: a1b2c3d4e5f6
Revises: 85552c1cd436
Create Date: 2026-03-16 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '85552c1cd436'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pnl column to trades
    op.add_column('trades', sa.Column('pnl', sa.Float(), nullable=True))

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('event_type', sa.String(), nullable=False, index=True),
        sa.Column('detail', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Create strategy_profiles table
    op.create_table(
        'strategy_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('profile', sa.String(), nullable=False, server_default='balanced'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )


def downgrade() -> None:
    op.drop_table('strategy_profiles')
    op.drop_table('audit_logs')
    op.drop_column('trades', 'pnl')
