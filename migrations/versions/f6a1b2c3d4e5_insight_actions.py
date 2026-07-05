"""insight actions

Revision ID: f6a1b2c3d4e5
Revises: e5f8a3b2c1d0
Create Date: 2026-07-04 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f6a1b2c3d4e5'
down_revision = 'e5f8a3b2c9e1d0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ai_insight', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('action_note', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('action_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('snoozed_until', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('ai_insight', schema=None) as batch_op:
        batch_op.drop_column('snoozed_until')
        batch_op.drop_column('action_at')
        batch_op.drop_column('action_note')
        batch_op.drop_column('status')
