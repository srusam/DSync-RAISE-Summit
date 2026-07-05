"""design handoff

Revision ID: d4a7b2c9e1f0
Revises: c8e2f1a9b3d4
Create Date: 2026-07-04 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4a7b2c9e1f0'
down_revision = 'c8e2f1a9b3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'design_handoff',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('figma_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('spec', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('finalized_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['figma_snapshot_id'], ['figma_snapshot.id']),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('design_handoff')
